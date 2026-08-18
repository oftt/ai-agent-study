"""
Stage 1 · 流式输出(打字机效果)
==============================
目标:不用等模型全部生成完,而是"边生成边显示"。

为什么重要:
  1. 用户体验 —— 大模型生成一段话要几秒,干等 vs 逐字蹦出,感觉天差地别
  2. 这也是后面 Agent "边思考边展示" 的基础
  3. 对长输出,还能提前看到开头,随时可中断,省 token

原理:stream=True 后,create() 返回一个迭代器,模型每生成一小块(token 块)
就吐出来一次,我们对每一块做增量处理。

运行:
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe stage01-basic-api/03_streaming.py
"""

import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

stream = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {"role": "system", "content": "你是 RAG 专家,回答简洁。"},
        {"role": "user", "content": "用 60 个字左右介绍什么是 RAG。"},
    ],
    stream=True,        # ← 开启流式
)

print("🤖 ", end="", flush=True)
for chunk in stream:                    # 每个 chunk 是模型吐出来的一小块
    # 流式模式下,内容在 chunk.choices[0].delta.content 里
    delta = chunk.choices[0].delta
    piece = delta.content if delta and delta.content else ""
    print(piece, end="", flush=True)    # flush=True 立即刷新到屏幕,不缓存
    time.sleep(0.03)                    # 模拟打字机节奏(可删掉看真实速度)

print("\n\n✅ 流式输出完成")
