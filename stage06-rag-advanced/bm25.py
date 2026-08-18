"""
Stage 6 · 手写 BM25 关键词检索
================================
BM25(Okapi BM25):信息检索经典算法,按"关键词词频 + 逆文档频率"打分。
为什么 RAG 需要它:
  - 向量检索按"语义"找,但对【精确术语、缩写、数字、编号】常失灵(如查 "OA 系统")
  - BM25 按"字面命中"找,恰好擅长这些
  - 两者互补 → 混合检索(见 hybrid_store.py)

打分公式:
  score(d,q) = Σ  idf(q) * [ tf(q,d) * (k1+1) ] / [ tf(q,d) + k1*(1 - b + b*|d|/avgdl) ]
  - tf(q,d)   词 q 在文档 d 中出现的次数(词频)
  - idf(q)    词 q 的稀有度:越稀有越值钱
  - k1, b     调参:k1 词频饱和, b 长度归一化(默认 k1=1.5, b=0.75)

中文分词用 jieba(把"员工手册"切成词,BM25 才能统计词频)。
"""

import math
from collections import Counter

import jieba

# 简易停用词:中英文常见虚词(课堂版,真实项目会维护更全的停用词表)
STOPWORDS = set("的了在是和与及等个之不也都就很被把让对从向为了于给和或但然而因为所以如果".strip())


def tokenize(text: str) -> list[str]:
    """中文分词 + 过滤空白/停用词。"""
    return [w for w in jieba.lcut(text) if w.strip() and w not in STOPWORDS]


class BM25:
    def __init__(self, corpus: list[str], k1: float = 1.5, b: float = 0.75):
        self.corpus = corpus
        self.doc_tokens = [tokenize(d) for d in corpus]   # 每篇文档切词
        self.doc_lens = [len(t) for t in self.doc_tokens]
        self.avgdl = sum(self.doc_lens) / max(len(self.doc_lens), 1)
        self.N = len(corpus)
        self.k1, self.b = k1, b

        # 文档频率 df:每个词出现在多少篇文档里(稀有度)
        self.df: Counter = Counter()
        for doc in self.doc_tokens:
            for w in set(doc):
                self.df[w] += 1

    def _idf(self, term: str) -> float:
        """逆文档频率:出现在越少文档里的词,权重越高。"""
        return math.log(1 + (self.N - self.df[term] + 0.5) / (self.df[term] + 0.5))

    def score(self, doc_idx: int, query_tokens: list[str]) -> float:
        """计算一篇文档对查询的 BM25 分数。"""
        dl = self.doc_lens[doc_idx]
        tf = Counter(self.doc_tokens[doc_idx])
        s = 0.0
        for q in query_tokens:
            f = tf.get(q, 0)
            if f:
                # 词频饱和:k1 防止"出现很多次"带来的分数无限涨
                tf_part = f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
                s += self._idf(q) * tf_part
        return s

    def search(self, query: str, top_k: int = 5) -> list[tuple[int, float]]:
        """返回 [(文档下标, 分数)],按分数降序,只保留分数>0 的。"""
        qt = tokenize(query)
        if not qt:
            return []
        scored = [(i, self.score(i, qt)) for i in range(self.N)]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [(i, s) for i, s in scored[:top_k] if s > 0]


if __name__ == "__main__":
    # 快速自测
    corpus = ["小明喜欢喝美式咖啡", "北京的秋天很美", "咖啡因能提神"]
    bm = BM25(corpus)
    print("查询「咖啡」:", [(corpus[i], round(s, 2)) for i, s in bm.search("咖啡")])
