"""
Stage 1 · 参数实验
==================
目标:亲手感受 temperature / max_tokens / top_p / seed 四个参数的效果。

观察点:
  A vs B    temperature 从 0 → 1.5,回答从"每次都一样"变成"每次不一样"
  C         max_tokens 太小时,输出会被截断(finish_reason = length)
  D vs D'   seed 相同 → 相同温度下,随机采样被固定,两次结果一致

运行:
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe stage01-basic-api/02_parameters.py
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

QUESTION = "请写一句描写春天的句子,要求有想象力。"


def ask(label: str, temperature=0.7, max_tokens=64, top_p=1.0, seed=None):
    resp = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": QUESTION}],
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        seed=seed,
    )
    msg = resp.choices[0].message
    print(f"\n--- {label}  (temperature={temperature}, max_tokens={max_tokens}, top_p={top_p}, seed={seed}) ---")
    print(f"回复: {msg.content}")
    # finish_reason 有四种:stop(正常结束) / length(被 max_tokens 截断)
    #                    / content_filter(被过滤) / tool_calls(要调用工具,Stage 2 见)
    print(f"finish_reason: {resp.choices[0].finish_reason}")


# A. 低温:几乎每次都一样(确定性)
ask("A", temperature=0.0)
ask("A'", temperature=0.0)

# B. 高温:每次都不一样(创造性)
ask("B", temperature=1.5)
ask("B'", temperature=1.5)

# C. 输出截断:max_tokens 设得很小
ask("C", max_tokens=5)

# D. 固定随机种子:同一 seed + 同一温度 → 结果可复现
ask("D", temperature=0.8, seed=42)
ask("D'", temperature=0.8, seed=42)
