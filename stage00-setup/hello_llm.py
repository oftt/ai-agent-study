"""
Stage 0 —— 第一次调用 LLM
==========================
目标:学会最基本的"把一句话发给大模型,拿到回复"。

这是所有 AI Agent 的地基 —— Agent 本质上就是在"反复调用大模型 + 执行工具"。
先把这一通电话打通。

运行方式(Windows 上 conda run 打印中文会崩溃,直接用环境里的 python):
    C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe stage00-setup/hello_llm.py
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

# 1. 从 .env 读取密钥(项目根目录下执行,dotenv 会自动向上查找)
load_dotenv()

# 2. 创建一个客户端 —— DeepSeek 的接口和 OpenAI 完全兼容,只是换了 base_url
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# 3. 构造一段"对话"
messages = [
    # system:给模型设定角色和规矩(可选,但强烈建议)
    {"role": "system", "content": "你是一位严谨的中文技术讲师,回答要简洁准确。"},
    # user:用户说的话
    {"role": "user", "content": "请用一句话告诉我:什么是 AI Agent?"},
]

# 4. 发送请求,拿到回复
response = client.chat.completions.create(
    model="deepseek-v4-flash",   # 指定使用的模型
    messages=messages,
    temperature=0,         # 0~2,越大越随机,越小越确定
)

# 5. 打印结果
reply = response.choices[0].message.content
print("=" * 50)
print("模型回复:", reply)
print("=" * 50)
print("本次用量: 输入 tokens =", response.usage.prompt_tokens,
      "| 输出 tokens =", response.usage.completion_tokens)
