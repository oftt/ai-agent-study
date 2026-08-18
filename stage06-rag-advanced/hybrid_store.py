"""
Stage 6 · 混合检索存储
=======================
在 Stage 5 向量检索的基础上,做三件进阶事:
  1. 元数据:分块时记录"所属章节",支持按章节过滤
  2. 混合检索:向量 + BM25 两路召回,用 RRF(倒数排名融合)合并
  3. LLM 重排:把候选片段交给模型"精排",取最相关的 top_k

两路召回各自的强项:
  向量   —— 语义相关(同义替换、意译都能找到)
  BM25   —— 字面命中(精确术语、缩写、数字、编号)
  RRF 融合 —— 两路都排前面的,分数高

LLM 重排(Cross-Encoder 的平替,国内环境不装重型模型):
  用模型直接看"问题 + 候选片段",判断相关性,只留最相关的。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # 以便 import lib

import numpy as np  # noqa: E402

from bm25 import BM25  # noqa: E402
from lib.embed import embed, embed_many  # noqa: E402
from lib.llm import MODEL, get_client  # noqa: E402

client = get_client()

DATA_FILE = Path(__file__).resolve().parent.parent / "stage05-rag" / "data" / "员工手册.md"
STORE_DIR = Path(__file__).resolve().parent / "store"


# ============ 分块(带章节元数据)============

def fixed_chunk(text: str, size: int, overlap: int) -> list[str]:
    if not text.strip():
        return []
    chunks, start, n = [], 0, len(text)
    while start < n:
        end = min(start + size, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = max(end - overlap, start + 1)
    return chunks


def section_chunk(text: str, chunk_size: int = 200, overlap: int = 30):
    """
    按 "## 章节" 分节,节内再定长分块。
    好处:每个片段都带着"它属于哪个章节"的元数据,可据此过滤。
    返回 (chunks, metas),metas[i] 是第 i 块的章节名。
    """
    sections: list[tuple[str, str]] = []
    title, buf = "前言", []
    for line in text.splitlines():
        if line.startswith("## "):
            if buf:
                sections.append((title, "\n".join(buf)))
            title = line[3:].strip()
            buf = []
        else:
            buf.append(line)
    if buf:
        sections.append((title, "\n".join(buf)))

    chunks, metas = [], []
    for t, body in sections:
        for c in fixed_chunk(body, chunk_size, overlap):
            chunks.append(c)
            metas.append(t)
    return chunks, metas


# ============ 混合存储 ============

class HybridStore:
    def __init__(self, path=STORE_DIR):
        self.path = Path(path)
        self.chunks: list[str] = []
        self.metas: list[str] = []
        self.vectors: np.ndarray | None = None
        self.bm25: BM25 | None = None

    # ----- 构建与持久化 -----

    def build(self) -> "HybridStore":
        raw = DATA_FILE.read_text(encoding="utf-8")
        self.chunks, self.metas = section_chunk(raw)
        self.vectors = np.array(embed_many(self.chunks))
        self.bm25 = BM25(self.chunks)
        self.save()
        return self

    def save(self) -> None:
        self.path.mkdir(parents=True, exist_ok=True)
        np.save(self.path / "vectors.npy", self.vectors)
        (self.path / "chunks.json").write_text(json.dumps(self.chunks, ensure_ascii=False), encoding="utf-8")
        (self.path / "metas.json").write_text(json.dumps(self.metas, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path=STORE_DIR) -> "HybridStore":
        s = cls(path)
        s.vectors = np.load(s.path / "vectors.npy")
        s.chunks = json.loads((s.path / "chunks.json").read_text(encoding="utf-8"))
        s.metas = json.loads((s.path / "metas.json").read_text(encoding="utf-8"))
        s.bm25 = BM25(s.chunks)          # BM25 索引内存重建(快)
        return s

    # ----- 三路检索 -----

    def vector_search(self, query: str, top_k: int = 5) -> list[tuple[int, float]]:
        qv = embed(query)
        qn = qv / (np.linalg.norm(qv) + 1e-9)
        vn = self.vectors / (np.linalg.norm(self.vectors, axis=1, keepdims=True) + 1e-9)
        scores = vn @ qn
        idx = np.argsort(-scores)[:top_k]
        return [(int(i), float(scores[i])) for i in idx]

    def bm25_search(self, query: str, top_k: int = 5) -> list[tuple[int, float]]:
        return self.bm25.search(query, top_k)

    def hybrid_search(self, query: str, top_k: int = 5, rrf_k: int = 60) -> list[tuple[int, float]]:
        """
        RRF 融合:把两路排序的"名次"折算成分数再相加。
        RRF 只看名次、不看原始分数 → 天然解决"向量分和 BM25 分不在一个量纲"的问题。
        """
        vector_hits = [i for i, _ in self.vector_search(query, top_k=10)]
        bm25_hits = [i for i, _ in self.bm25_search(query, top_k=10)]

        fused: dict[int, float] = {}
        for rank, i in enumerate(vector_hits):
            fused[i] = fused.get(i, 0) + 1 / (rrf_k + rank + 1)
        for rank, i in enumerate(bm25_hits):
            fused[i] = fused.get(i, 0) + 1 / (rrf_k + rank + 1)

        ordered = sorted(fused, key=lambda i: fused[i], reverse=True)
        return [(i, fused[i]) for i in ordered[:top_k]]

    # ----- 元数据过滤 -----

    def filter_by_meta(self, ids: list[int], keyword: str) -> list[int]:
        """只保留章节名包含 keyword 的片段下标。"""
        return [i for i in ids if keyword in self.metas[i]]

    # ----- LLM 重排 -----

    def llm_rerank(self, query: str, candidates: list[int], top_k: int = 3) -> list[int]:
        """让模型从候选里挑最相关的 top_k 个,按相关性排序。"""
        numbered = "\n".join(f"[{i}] {self.chunks[i][:100]}..." for i in candidates)
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{
                "role": "user",
                "content": (
                    f"问题:{query}\n\n候选片段(编号在前):\n{numbered}\n\n"
                    f"请挑选最相关的 {top_k} 个片段,只输出 JSON:"
                    f'{{"order": [编号, 编号, ...]}},按相关性从高到低排列。'
                ),
            }],
            response_format={"type": "json_object"},
            temperature=0,
        )
        try:
            order = json.loads(resp.choices[0].message.content)["order"]
            picked = [int(x) for x in order if int(x) in candidates]
            picked = picked[:top_k]
            return picked + [i for i in candidates if i not in picked]  # 兜底补全
        except Exception:
            return candidates[:top_k]     # 解析失败 → 保持原顺序

    def __len__(self) -> int:
        return len(self.chunks)


if __name__ == "__main__":
    if not (STORE_DIR / "vectors.npy").exists():
        print("首次运行,构建索引...")
        store = HybridStore().build()
    else:
        store = HybridStore.load()
    print(f"索引就绪:{len(store)} 个片段")
    for q in ["OA 系统是什么", "五险一金", "年假几天"]:
        print(f"\n查询: {q}")
        print("  向量 top3:", [(store.chunks[i][:20].replace('\n',''), round(s,2)) for i,s in store.vector_search(q,3)])
        print("  BM25 top3:", [(store.chunks[i][:20].replace('\n',''), round(s,2)) for i,s in store.bm25_search(q,3)])
        print("  混合 top3:", [(store.chunks[i][:20].replace('\n',''), round(s,2)) for i,s in store.hybrid_search(q,3)])
