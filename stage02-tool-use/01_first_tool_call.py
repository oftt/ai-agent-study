"""
Stage 2 · 第一次工具调用
========================
目标:让模型"决定"调用一个工具,并看清它返回的"调用指令"长什么样。

关键概念 —— 工具调用的完整流程(4 步):
  1. 定义工具:告诉模型有哪些工具可用(tools 参数,含 name/description/参数schema)
  2. 模型思考:模型觉得需要工具时,不直接回答,而是返回 tool_calls 指令
  3. 我们执行:程序真正去调用那个函数(比如查天气 API)
  4. 结果回填:把工具结果作为 tool 角色消息喂回,让模型据此给出最终回答

本脚本只演示前 2 步:看清"模型想调用谁、参数是什么"。
真正的执行在 02_tool_loop.py。

运行:
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe stage02-tool-use/01_first_tool_call.py
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# ---- 1. 定义工具(本质是给模型看的"说明书")----
# parameters 是 JSON Schema:说明函数要什么参数
tools = [
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

# ---- 2. 发送请求(带上 tools)----
resp = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {"role": "user", "content": "北京现在天气怎么样?顺便看看现在几点了。"},
    ],
    tools=tools,
    temperature=0.3,
)

msg = resp.choices[0].message
print("finish_reason:", resp.choices[0].finish_reason)
print("=" * 60)
print("模型没有直接回答,而是返回了工具调用指令:")
print()

if msg.tool_calls:
    for i, call in enumerate(msg.tool_calls, 1):
        print(f"调用 #{i}")
        print(f"  要调用的工具名: {call.function.name}")
        print(f"  参数(JSON字符串): {call.function.arguments}")
        # 参数是 JSON 字符串,需要 json.loads 解析成 dict
        args = json.loads(call.function.arguments)
        print(f"  解析后的参数: {args}")
        print()
else:
    print("模型没有调用工具,直接回答:", msg.content)
