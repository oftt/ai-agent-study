"""
Stage 1 · 结构化输出(JSON + Pydantic 校验)
==========================================
目标:让模型输出"严格符合我们定义的格式"的 JSON。

为什么重要:
  这是通往 Stage 2(工具调用)的关键一步 —— 让模型返回结构化数据,
  程序才能可靠地解析并执行。JSON 乱七八糟的话,后面一切自动化都会崩。

三段式套路(请背下来,后面全程用到):
  1. 用 Pydantic 定义期望结构 → 转成 JSON Schema
  2. 把 Schema 告诉模型(放 system 里)+ 指定 response_format="json_object"
  3. 解析返回的 JSON,再用 Pydantic 校验(字段缺失/类型错/超范围 → 抛错)

运行:
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe stage01-basic-api/04_structured_output.py
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)


# ---- 1. 用 Pydantic 定义期望的输出结构(用于最终校验)----
class MovieReview(BaseModel):
    title: str = Field(description="电影名")
    rating: float = Field(ge=0, le=10, description="评分,0~10")
    pros: list[str] = Field(description="至少 2 条优点")
    cons: list[str] = Field(description="至少 1 条缺点")
    summary: str = Field(description="一句话总评")


# ---- 2. 请求模型输出 JSON ----
# 🕳️ 踩坑:不要直接把 JSON Schema 塞给模型 —— 模型会"原样抄作业"把 Schema 当输出。
#    更稳的做法:文字描述字段 + 给一个"输出示例"(示例长什么样,模型就照着长什么样)。
example = (
    '{"title": "流浪地球2", "rating": 8.5, '
    '"pros": ["特效震撼", "科幻硬核"], '
    '"cons": ["叙事偏长"], '
    '"summary": "中国科幻里程碑。"}'
)

resp = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {"role": "system", "content": (
            "你是影评人。只输出 JSON,不要任何多余文字,不要输出 schema 定义。\n"
            "字段要求:\n"
            '- "title": 电影名(字符串)\n'
            '- "rating": 评分(0~10 的数字)\n'
            '- "pros": 优点(字符串数组,至少 2 个)\n'
            '- "cons": 缺点(字符串数组,至少 1 个)\n'
            '- "summary": 一句话总评(字符串)\n'
            f"输出示例:\n{example}\n"
            "现在请评价:"
        )},
        {"role": "user", "content": "请评价电影《流浪地球2》"},
    ],
    response_format={"type": "json_object"},   # ← 强制 JSON 格式输出
    temperature=0.3,                            # 结构化输出用低温更稳
)

raw = resp.choices[0].message.content
print("模型原始输出:", raw)

# ---- 3. 解析 + 校验 ----
data = json.loads(raw)                      # 字符串 → dict
review = MovieReview.model_validate(data)   # 校验:类型、范围不符会直接抛错

print("\n✅ 解析 + 校验通过:")
print(review.model_dump_json(indent=2))   # model_dump_json 才支持 indent
print("\n评分:", review.rating, "| 优点数:", len(review.pros))
