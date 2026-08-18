"""
Stage 4 · 长期记忆:向量检索记忆
================================
短期记忆只管"最近聊了啥"。长期记忆要解决:
  哪怕跨了很多天,用户问"我以前说过什么",Agent 也能想起来。

原理(三步):
  1. 存储:把要记住的事实 embedding 成向量,存起来
  2. 检索:把当前问题也 embedding,算所有记忆的相似度(余弦),取最相关的几条
  3. 注入:把检索到的记忆塞进 system prompt,让模型回答时参考

这不就是"迷你 RAG"吗?没错 —— 长期记忆 = 对"自己的历史"做检索增强。

运行:
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe stage04-memory/vector_memory.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # 以便 import lib

import numpy as np  # noqa: E402

from lib.embed import embed  # noqa: E402
from lib.llm import MODEL, get_client  # noqa: E402

client = get_client()


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """余弦相似度:1=完全一致,0=无关,越接近 1 越相关。"""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


class VectorMemory:
    """一个极简的内存版向量记忆库(真实项目用向量数据库,Stage 5 会做)。"""

    def __init__(self, top_k: int = 3):
        self.top_k = top_k
        self.facts: list[str] = []            # 记忆条目
        self.vectors: list[np.ndarray] = []   # 对应的向量

    def add(self, fact: str) -> None:
        """记住一条事实。"""
        self.facts.append(fact)
        self.vectors.append(embed(fact))      # 关键:存的是向量
        print(f"  💾 记住: {fact}")

    def search(self, query: str, top_k: int | None = None) -> list[tuple[str, float]]:
        """检索与 query 最相关的 top_k 条记忆,返回 (文本, 相似度)。"""
        k = top_k or self.top_k
        if not self.facts:
            return []
        qv = embed(query)
        scores = [(self.facts[i], cosine(qv, self.vectors[i])) for i in range(len(self.facts))]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]

    def recall(self, query: str) -> str:
        """把检索结果拼成一段文本,方便塞进提示词。"""
        hits = self.search(query)
        if not hits:
            return "(没有相关记忆)"
        return "\n".join(f"- {text} (相似度 {score:.2f})" for text, score in hits)


def ask_with_memory(question: str, memory: VectorMemory) -> str:
    """标准做法:检索相关记忆 → 注入 system → 模型回答。"""
    related = memory.recall(question)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": (
                "你是一个贴心的私人助理。下面是关于用户的长期记忆,回答时参考,不要编造:\n"
                + related
            )},
            {"role": "user", "content": question},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    memory = VectorMemory(top_k=2)

    # 模拟"长期积累"的记忆(现实中会在每次对话后自动提取存入)
    print("=== 长期记忆库(积累中)===")
    for fact in [
        "用户小明的生日是 3 月 14 日",
        "小明喜欢喝美式咖啡,不加糖",
        "小明是一位后端程序员,正在学 AI Agent 开发",
        "小明有一只叫「团子」的橘猫",
        "小明最近在健身,目标是减重 5 公斤",
    ]:
        memory.add(fact)

    print("\n=== 测试记忆检索 ===")
    for q in ["他喜欢喝什么?", "我什么时候过生日?", "他在减肥吗?", "关于他的猫,你知道什么?"]:
        print(f"\n问: {q}")
        print("检索到的记忆:")
        for text, score in memory.search(q):
            print(f"  · [{score:.2f}] {text}")
        print("回答:", ask_with_memory(q, memory))
