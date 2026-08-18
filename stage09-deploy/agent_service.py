"""
Stage 9 · 服务端 Agent 核心(与 Web 层解耦)
============================================
一个能部署的 Agent 服务应该具备的工程能力:
  1. 会话记忆   —— 按 session_id 管理多轮上下文(滑动窗口裁剪)
  2. 工具调用   —— 复用 Stage 2/3 的循环,且支持流式
  3. 流式输出   —— stream_chat 是个生成器,逐块吐出文本(给 SSE 用)
  4. 用量统计   —— 每次流式结束后累加 token 与费用
  5. 工具缓存   —— TTLCache 缓存天气等重复调用,省钱省时
  6. 日志       —— 关键节点打日志(在 app.py 配置)

stream_chat 的流式 + 工具调用技巧:
  - 工具调用发生在流的中后段;tool_calls 的 delta 里没有 content → 前端不会看到杂音
  - 用 stream_options={"include_usage": True} 拿到每轮流式的用量
"""

import json
import logging
import sys
import time
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.llm import MODEL, get_client  # noqa: E402
from usage import UsageTracker  # noqa: E402

logger = logging.getLogger("agent_service")


# ============ 工具缓存 ============

class TTLCache:
    """带过期时间的简单缓存(演示:降低重复工具调用的成本与延迟)。"""

    def __init__(self, ttl: float = 300):
        self.ttl = ttl                       # 过期秒数
        self._data: OrderedDict[str, tuple[float, object]] = OrderedDict()

    def get(self, key: str):
        item = self._data.get(key)
        if item is None:
            return None
        ts, value = item
        if time.time() - ts > self.ttl:
            del self._data[key]              # 过期即删
            return None
        return value

    def set(self, key: str, value) -> None:
        self._data[key] = (time.time(), value)


# ============ 工具定义 ============

def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_weather(city: str) -> str:
    """模拟天气(真实项目换成 API 调用)。"""
    fake = {"北京": "晴,25°C", "上海": "多云,28°C", "广州": "雷阵雨,30°C"}
    return fake.get(city, f"{city}:暂无数据")


def calculate(expr: str) -> str:
    """计算简单四则运算表达式(白名单方式,防注入)。"""
    allowed = set("0123456789+-*/(). ")
    if not set(expr) <= allowed:
        return "表达式包含非法字符"
    return str(eval(expr, {"__builtins__": {}}, {}))


TOOLS_SCHEMA = [
    {"type": "function", "function": {
        "name": "get_current_time", "description": "获取当前日期和时间",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "get_weather", "description": "查询指定城市的当前天气",
        "parameters": {"type": "object", "properties": {
            "city": {"type": "string", "description": "城市名,例如 北京"}}, "required": ["city"]}}},
    {"type": "function", "function": {
        "name": "calculate", "description": "计算四则运算,例如 (12+5)*3",
        "parameters": {"type": "object", "properties": {
            "expr": {"type": "string", "description": "四则运算表达式"}}, "required": ["expr"]}}},
]


# ============ 聊天 Agent ============

class ChatAgent:
    def __init__(self, max_memory: int = 20, usage: UsageTracker | None = None):
        self.sessions: dict[str, list[dict]] = {}
        self.max_memory = max_memory
        self.usage = usage or UsageTracker()
        self._weather_cache = TTLCache(ttl=300)      # 工具缓存实例

    # ----- 记忆 -----

    def _get_messages(self, session_id: str) -> list[dict]:
        if session_id not in self.sessions:
            self.sessions[session_id] = [
                {"role": "system", "content": (
                    "你是服务端 AI 助手,能用工具查时间、查天气、算数。回答简洁自然。"
                )}
            ]
        return self.sessions[session_id]

    def _trim(self, messages: list[dict]) -> None:
        """滑动窗口:保留 system + 最近 max_memory 条。"""
        if len(messages) > self.max_memory + 1:
            excess = len(messages) - self.max_memory - 1
            del messages[1:1 + excess]

    # ----- 工具执行 -----

    def _execute(self, name: str, args_json: str) -> str:
        try:
            args = json.loads(args_json or "{}")
            if name == "get_weather":                     # 演示缓存:同一城市 5 分钟内不重查
                key = args.get("city", "")
                cached = self._weather_cache.get(key)
                if cached:
                    logger.info("命中天气缓存 city=%s", key)
                    return cached
                result = str(get_weather(**args))
                self._weather_cache.set(key, result)
                return result
            impl = {"get_current_time": get_current_time, "calculate": calculate}[name]
            return str(impl(**args))
        except Exception as e:
            return f"工具执行出错: {type(e).__name__}: {e}"

    # ----- 流式对话(生成器)-----

    def stream_chat(self, session_id: str, message: str):
        """
        生成器:逐块 yield {"delta": 文本}。遇到工具调用则静默执行并继续。
        结束前 yield {"delta": "", "done": True}。
        """
        messages = self._get_messages(session_id)
        messages.append({"role": "user", "content": message})
        logger.info("开始处理 session=%s 消息len=%d", session_id, len(message))

        for _round in range(5):                          # 工具循环上限
            stream = get_client().chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS_SCHEMA,
                temperature=0.5,
                stream=True,
                stream_options={"include_usage": True},   # 流式也要拿用量
            )

            content_parts, tool_acc, finish, usage = [], {}, None, None
            for chunk in stream:
                if getattr(chunk, "usage", None):        # 流结束的 usage chunk
                    usage = chunk.usage
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                finish = choice.finish_reason
                delta = choice.delta

                if delta.content:
                    content_parts.append(delta.content)
                    yield {"delta": delta.content}       # 前端逐字显示

                if getattr(delta, "tool_calls", None):
                    for tc in delta.tool_calls:          # 流式 tool_calls 需要拼接
                        acc = tool_acc.setdefault(tc.index, {"id": "", "name": "", "arguments": ""})
                        if tc.id:
                            acc["id"] = tc.id
                        if tc.function.name:
                            acc["name"] += tc.function.name
                        if tc.function.arguments:
                            acc["arguments"] += tc.function.arguments

            if usage:
                self.usage.add(usage.prompt_tokens, usage.completion_tokens)

            content = "".join(content_parts)

            if finish == "tool_calls":
                logger.info("模型请求 %d 个工具", len(tool_acc))
                tool_calls = [{"id": a["id"], "type": "function",
                               "function": {"name": a["name"], "arguments": a["arguments"]}}
                              for a in tool_acc.values()]
                messages.append({"role": "assistant", "content": content or None, "tool_calls": tool_calls})
                for a in tool_acc.values():
                    result = self._execute(a["name"], a["arguments"])
                    logger.info("工具 %s -> %s", a["name"], result[:40])
                    messages.append({"role": "tool", "tool_call_id": a["id"], "content": result})
                continue

            messages.append({"role": "assistant", "content": content})
            break

        self._trim(messages)
        yield {"delta": "", "done": True}


if __name__ == "__main__":
    # 简单自测(不走 Web)
    agent = ChatAgent()
    print("回答:", end="")
    for ev in agent.stream_chat("demo-session", "现在几点了?"):
        if ev.get("delta"):
            print(ev["delta"], end="", flush=True)
    print("\n" + agent.usage.summary())
