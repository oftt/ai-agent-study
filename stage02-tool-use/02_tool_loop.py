"""
Stage 2 · 完整的工具调用循环
============================
目标:补全"工具调用"的 4 步中的第 3、4 步 —— 真正执行工具 + 结果回填,
并把这个过程循环起来,直到模型给出最终答案。

这就是一个"微型 Agent":模型负责决定做什么,我们负责执行。

核心循环(请背下来,Stage 3 会把它升级成正式 Agent):
  1. 调用模型(带 tools)
  2. 看回复:
     - 有 tool_calls → 逐个执行工具,把结果以 role="tool" 消息回填 → 回到 1
     - 没有 tool_calls → 那就是最终答案,结束

运行:
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe stage02-tool-use/02_tool_loop.py
"""

import json
import os
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# ================= 工具定义(函数实现)=================

def get_weather(city: str) -> str:
    """模拟天气查询(真实项目里这里调用天气 API)"""
    fake = {"北京": "晴,25°C", "上海": "多云,28°C", "广州": "雷阵雨,30°C"}
    return fake.get(city, f"{city}:暂无数据")


def get_current_time() -> str:
    """获取当前时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 工具注册表:name -> 函数(执行工具时按名字找到它)
TOOLS_IMPL = {
    "get_weather": get_weather,
    "get_current_time": get_current_time,
}

# 给模型看的"说明书"(与 TOOLS_IMPL 一一对应)
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的当前天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名,例如 北京"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前日期和时间",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def run_with_tools(user_question: str, max_rounds: int = 5) -> str:
    """
    工具调用循环。返回模型最终回答。
    max_rounds: 防止死循环(模型反复调工具不收敛)
    """
    messages = [{"role": "user", "content": user_question}]

    for round_no in range(max_rounds):
        resp = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=messages,
            tools=TOOLS_SCHEMA,
            temperature=0.3,
        )
        msg = resp.choices[0].message

        # 情况 1:模型没有要调用工具 → 这就是最终答案
        if not msg.tool_calls:
            return msg.content

        # 情况 2:模型要调用工具 → 我们执行,结果回填
        print(f"\n🔄 第 {round_no+1} 轮:模型请求调用 {len(msg.tool_calls)} 个工具")

        # 先把模型的"调用指令"存入历史(角色是 assistant,但带 tool_calls)
        messages.append(msg)   # msg 本身携带 tool_calls 字段,直接存

        for call in msg.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments)
            print(f"   ▶ 执行 {name}({args})")

            # 真正执行工具
            result = TOOLS_IMPL[name](**args)
            print(f"     ← 结果: {result}")

            # 把工具结果回填:role="tool",必须带上 tool_call_id 与指令对应
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": str(result),
            })

    return "(达到最大轮数,强制结束。模型未给出最终回答。)"  # 兜底


# ---- 演示:一个需要两次工具调用的任务 ----
answer = run_with_tools("北京现在天气怎么样?顺便告诉我现在几点了。")
print("\n" + "=" * 60)
print("🤖 最终回答:", answer)
