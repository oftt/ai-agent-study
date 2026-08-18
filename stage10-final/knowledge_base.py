"""
毕业项目 · 知识库(RAG)
========================
把 data/ 目录下的文档建成可检索的知识库。
复用 Stage 6 的部件:section_chunk(带章节元数据)、BM25、RRF 混合检索。

对外暴露:
  KnowledgeBase.build()   从 data/ 构建索引并保存
  KnowledgeBase.load()    从磁盘加载
  KnowledgeBase.search_knowledge(query)  ← 供 Agent 作为工具调用
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "stage06-rag-advanced"))   # 复用 bm25.py

import numpy as np  # noqa: E402

from bm25 import BM25  # noqa: E402
from lib.embed import embed, embed_many  # noqa: E402

DATA_DIR = Path(__file__).parent / "data"
STORE_DIR = Path(__file__).parent / "store"


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


def section_chunk(text: str, chunk_size: int = 220, overlap: int = 30):
    """按 "## 章节" 分节,节内分块,记录章节元数据。"""
    sections = []
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


class KnowledgeBase:
    def __init__(self, data_dir=DATA_DIR, store_dir=STORE_DIR):
        self.data_dir = Path(data_dir)
        self.store_dir = Path(store_dir)
        self.chunks: list[str] = []
        self.metas: list[str] = []            # 每块的"文件名·章节"
        self.vectors: np.ndarray | None = None
        self.bm25: BM25 | None = None

    # ----- 构建 -----

    def build(self) -> "KnowledgeBase":
        self.chunks, self.metas = [], []
        for md in sorted(self.data_dir.glob("*.md")):
            raw = md.read_text(encoding="utf-8")
            cs, ms = section_chunk(raw)
            self.chunks += cs
            self.metas += [f"{md.stem} · {m}" for m in ms]
            print(f"  入库 {md.name}:{len(cs)} 块")
        self.vectors = np.array(embed_many(self.chunks))
        self.bm25 = BM25(self.chunks)
        self.save()
        return self

    def save(self) -> None:
        self.store_dir.mkdir(parents=True, exist_ok=True)
        np.save(self.store_dir / "vectors.npy", self.vectors)
        (self.store_dir / "chunks.json").write_text(json.dumps(self.chunks, ensure_ascii=False), encoding="utf-8")
        (self.store_dir / "metas.json").write_text(json.dumps(self.metas, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, store_dir=STORE_DIR) -> "KnowledgeBase":
        kb = cls(store_dir=store_dir)
        kb.vectors = np.load(kb.store_dir / "vectors.npy")
        kb.chunks = json.loads((kb.store_dir / "chunks.json").read_text(encoding="utf-8"))
        kb.metas = json.loads((kb.store_dir / "metas.json").read_text(encoding="utf-8"))
        kb.bm25 = BM25(kb.chunks)
        return kb

    # ----- 检索 -----

    def _vector_ids(self, query: str, top_k: int) -> list[int]:
        qv = embed(query)
        qn = qv / (np.linalg.norm(qv) + 1e-9)
        vn = self.vectors / (np.linalg.norm(self.vectors, axis=1, keepdims=True) + 1e-9)
        return [int(i) for i in np.argsort(-(vn @ qn))[:top_k]]

    def hybrid_search(self, query: str, top_k: int = 4) -> list[tuple[int, float, str]]:
        """向量 + BM25 用 RRF 融合,返回 [(下标, 融合分, 章节)]。"""
        k = 60
        v = self._vector_ids(query, 8)
        b = [i for i, _ in self.bm25.search(query, 8)]
        fused: dict[int, float] = {}
        for rank, i in enumerate(v):
            fused[i] = fused.get(i, 0) + 1 / (k + rank + 1)
        for rank, i in enumerate(b):
            fused[i] = fused.get(i, 0) + 1 / (k + rank + 1)
        ordered = sorted(fused, key=lambda i: fused[i], reverse=True)[:top_k]
        return [(i, fused[i], self.metas[i]) for i in ordered]

    def search_knowledge(self, query: str) -> str:
        """给 Agent 用的工具接口:检索并格式化为文本。"""
        hits = self.hybrid_search(query, top_k=3)
        if not hits:
            return "知识库中没有相关内容。"
        parts = [f"[{self.metas[i]}] {self.chunks[i]}" for i, _, _ in hits]
        return "\n\n".join(parts)

    def __len__(self):
        return len(self.chunks)


if __name__ == "__main__":
    if (STORE_DIR / "vectors.npy").exists():
        kb = KnowledgeBase.load()
    else:
        print("构建知识库...")
        kb = KnowledgeBase().build()
    print(f"知识库就绪:{len(kb)} 个片段\n")
    for q in ["ReAct 的循环包括哪几步?", "RAG 为什么能减少幻觉?", "多智能体有哪两种模式?"]:
        print(f"问:{q}\n{ kb.search_knowledge(q)[:180] }\n")
