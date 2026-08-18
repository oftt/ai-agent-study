"""
毕业项目 · 完整 Agent
======================
把前 9 个阶段的能力整合成一个可部署的 Agent:
  - 工具调用循环(Stage 2/3):search_knowledge(RAG) + get_current_time + calculate
  - RAG 检索(Stage 5/6):知识库混合检索,让回答"有据可查"
  - 记忆(Stage 4):滑动窗口管理多轮上下文
  - 流式输出 + 用量统计(Stage 9)
  - 错误兜底:工具挂了变成观察喂回模型,让它自救

这也是对"一个 Agent 由什么组成"的最终答案:
  Agent = LLM + 工具 + 记忆 + (RAG 知识) + 工程化外壳
"""

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "stage09-deploy"))   # 复用 usage.py

from lib.llm import MODEL, get_client  # noqa: E402
from usage import UsageTracker  # noqa: E402

from knowledge_base import KnowledgeBase  # noqa: E402


# ---- 内置工具 ----

def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate(expr: str) -> str:
    allowed = set("0123456789+-*/(). ")
    if not set(expr) <= allowed:
        return "表达式包含非法字符"
    return str(eval(expr, {"__builtins__": {}}, {}))


class FinalAgent:
    def __init__(self, kbase: KnowledgeBase, max_memory: int = 16):
        self.kbase = kbase
        self.sessions: dict[str, list[dict]] = {}
        self.max_memory = max_memory
        self.usage = UsageTracker(log_file="final_usage.json")

        self.tools_schema = [
            {"type": "function", "function": {
                "name": "search_knowledge",
                "description": "在个人知识库中检索与问题相关的资料。遇到知识问题应优先调用。",
                "parameters": {"type": "object", "properties": {
                    "query": {"type": "string", "description": "检索关键词或问题"}},
                    "required": ["query"]}}},
            {"type": "function", "function": {
                "name": "get_current_time",
                "description": "获取当前日期和时间",
                "parameters": {"type": "object", "properties": {}}}},
            {"type": "function", "function": {
                "name": "calculate",
                "description": "计算四则运算,例如 (12+5)*3",
                "parameters": {"type": "object", "properties": {
                    "expr": {"type": "string", "description": "四则运算表达式"}},
                    "required": ["expr"]}}},
        ]
        self.tools_impl = {
            # kbase 可为空(纯记忆/计算测试用)
            "search_knowledge": kbase.search_knowledge if kbase else (lambda query: "知识库未加载"),
            "get_current_time": get_current_time,
            "calculate": calculate,
        }

    # ---- 记忆 ----

    def _get_messages(self, session_id: str) -> list[dict]:
        if session_id not in self.sessions:
            self.sessions[session_id] = [
                {"role": "system", "content": (
                    "你是个人知识库助理。回答知识问题前先调用 search_knowledge 检索资料,"
                    "再基于资料回答,资料没有就如实说明。也可查时间、算数。回答简洁。"
                )}
            ]
        return self.sessions[session_id]

    def _trim(self, messages: list[dict]) -> None:
        if len(messages) > self.max_memory + 1:
            excess = len(messages) - self.max_memory - 1
            del messages[1:1 + excess]

    # ---- 工具 ----

    def _execute(self, name: str, args_json: str) -> str:
        try:
            args = json.loads(args_json or "{}")
            return str(self.tools_impl[name](**args))
        except Exception as e:
            return f"工具执行出错: {type(e).__name__}: {e}"

    # ---- 流式对话 ----

    def stream_chat(self, session_id: str, message: str):
        messages = self._get_messages(session_id)
        messages.append({"role": "user", "content": message})

        for _round in range(5):
            stream = get_client().chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=self.tools_schema,
                temperature=0.4,
                stream=True,
                stream_options={"include_usage": True},
            )

            content_parts, tool_acc, finish, usage = [], {}, None, None
            for chunk in stream:
                if getattr(chunk, "usage", None):
                    usage = chunk.usage
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                finish = choice.finish_reason
                delta = choice.delta

                if delta.content:
                    content_parts.append(delta.content)
                    yield {"delta": delta.content}

                if getattr(delta, "tool_calls", None):
                    for tc in delta.tool_calls:
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
                tool_calls = [{"id": a["id"], "type": "function",
                               "function": {"name": a["name"], "arguments": a["arguments"]}}
                              for a in tool_acc.values()]
                messages.append({"role": "assistant", "content": content or None, "tool_calls": tool_calls})
                for a in tool_acc.values():
                    result = self._execute(a["name"], a["arguments"])
                    messages.append({"role": "tool", "tool_call_id": a["id"], "content": result})
                continue

            messages.append({"role": "assistant", "content": content})
            break

        self._trim(messages)
        yield {"delta": "", "done": True}


if __name__ == "__main__":
    from pathlib import Path as P
    store = P(__file__).parent / "store"
    kb = KnowledgeBase.load(store) if (store / "vectors.npy").exists() else KnowledgeBase().build()
    agent = FinalAgent(kb)
    for q in ["ReAct 的循环包括哪几步?", "再给我算一下 77*88"]:
        print(f"\n问: {q}\n答: ", end="", flush=True)
        for ev in agent.stream_chat("demo", q):
            if ev.get("delta"):
                print(ev["delta"], end="", flush=True)
        print()
    print(agent.usage.summary())
