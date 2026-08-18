"""
Stage 7 · 反思(Reflection)模式
===============================
让 Agent"自我审视 + 自我改进"的循环:

  Generate(生成)  → Critique(评审) → Revise(重写) → 再评审...

为什么有效:
  - 大模型一次生成往往不够好;但让它"挑自己的毛病"往往挑得准
  - 把"评价"和"写作"分开,各自专注,质量更高
  - 类似人类的"先写草稿,再改稿"

流程:
  1. 生成初稿
  2. 让模型扮演"挑剔的评审",指出问题(逻辑/风格/准确性)
  3. 让模型根据意见重写
  4. 循环 N 轮
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.llm import MODEL, get_client  # noqa: E402

client = get_client()


def _chat(system: str, user: str, temperature: float = 0.6) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=temperature,
    )
    return resp.choices[0].message.content.strip()


def generate(question: str) -> str:
    return _chat("你是一个文字创作者,输出质量高、有细节的作品。", question)


def critique(question: str, draft: str) -> str:
    """扮演挑剔的评审,指出具体问题。"""
    return _chat(
        "你是严格的文案评审。只挑毛病:逻辑漏洞、表述啰嗦、缺乏吸引力、偏离主题、缺少细节。"
        "给出 3~5 条具体的改进建议,用编号列出,不要客气。",
        f"题目:{question}\n\n草稿:\n{draft}",
        temperature=0.4,
    )


def revise(question: str, draft: str, feedback: str) -> str:
    """根据评审意见重写。"""
    return _chat(
        "你是文字创作者。根据评审意见,重写作品,逐条吸收建议,保留优点,输出最终版(不要解释过程)。",
        f"题目:{question}\n\n原稿:\n{draft}\n\n评审意见:\n{feedback}",
        temperature=0.6,
    )


def reflect(question: str, rounds: int = 2) -> str:
    """Generate → Critique → Revise 循环 rounds 轮,返回最终稿。"""
    draft = generate(question)
    print(f"📝 初稿({len(draft)} 字):\n{draft[:200]}\n")

    for i in range(1, rounds + 1):
        print(f"\n{'='*60}\n🔄 第 {i} 轮反思\n{'='*60}")
        feedback = critique(question, draft)
        print(f"\n🔍 评审意见:\n{feedback}\n")
        draft = revise(question, draft, feedback)
        print(f"\n✏️  重写稿({len(draft)} 字):\n{draft[:200]}\n")

    return draft
