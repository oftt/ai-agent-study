"""
Stage 1 · 多轮对话
==================
目标:让模型"记得"上下文,连续聊好几轮。

关键点:
  每一轮,都要把【你问的 + 模型答的】都追加进 messages 列表,
  下次调用时一起发给模型 —— 模型"记住"的前提是它每次都能看到完整历史。

运行:
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe stage01-basic-api/01_multi_turn.py
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# 初始只有 system + 用户第一问;assistant 的回答会动态追加进来
messages = [
    {"role": "system", "content": "你是孙悟空,语气要带上猴味,回答简短、略带自嘲。"},
]


def chat(user_text: str) -> str:
    """发一条消息,返回模型回复,并把这次问答追加进历史。"""
    messages.append({"role": "user", "content": user_text})

    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=messages,          # ← 传的是"全部历史",不是只传当前这句
        temperature=0.7,
    )
    reply = response.choices[0].message.content

    # 关键:把自己的回答也存进历史,下次它才知道"我说过什么"
    messages.append({"role": "assistant", "content": reply})
    return reply


# ---- 连续对话 ----
print("你:你是谁?")
print("悟空:", chat("你是谁?"))

print("\n你:那你会翻筋斗云吗?")
print("悟空:", chat("那你会翻筋斗云吗?"))

print("\n你:我刚才问你,你自己说你是什么来着?")
print("悟空:", chat("我刚才问你,你自己说你是什么来着? 你记得我们前面聊了什么吗?"))
