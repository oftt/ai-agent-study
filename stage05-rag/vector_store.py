"""
Stage 5 · 持久化向量库
=======================
把文档片段存成向量,并保存到磁盘,下次直接加载(不用重新 embedding)。

设计要点:
  - 用 numpy 存所有向量(一个矩阵),检索用向量化点积,快
  - 余弦相似度 = 归一化后的点积
  - save()/load():chunks.json + vectors.npy 持久化

真实项目会用专用向量数据库(ChromaDB / Milvus / Qdrant),原理一样,
本实现是为了"看得见摸得着"地理解向量库在干什么。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # 以便 import lib

import numpy as np  # noqa: E402

from lib.embed import embed, embed_many  # noqa: E402


class PersistentVectorStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.chunks: list[str] = []
        self.vectors: np.ndarray | None = None    # shape (N, D) 的矩阵

    # ---------- 写入 ----------

    def add_documents(self, docs: list[str]) -> None:
        """批量加入文档片段并向量化。"""
        self.chunks.extend(docs)
        new_vecs = np.array(embed_many(docs))
        self.vectors = new_vecs if self.vectors is None else np.vstack([self.vectors, new_vecs])

    def save(self) -> None:
        self.path.mkdir(parents=True, exist_ok=True)
        np.save(self.path / "vectors.npy", self.vectors)
        (self.path / "chunks.json").write_text(
            json.dumps(self.chunks, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ---------- 读取 ----------

    @classmethod
    def load(cls, path: str | Path) -> "PersistentVectorStore":
        p = Path(path)
        store = cls(p)
        store.vectors = np.load(p / "vectors.npy")
        store.chunks = json.loads((p / "chunks.json").read_text(encoding="utf-8"))
        return store

    # ---------- 检索 ----------

    def search(self, query: str, top_k: int = 3) -> list[tuple[str, float]]:
        """返回 (片段文本, 相似度) 列表,按相似度从高到低。"""
        qv = embed(query)
        # 归一化后点积 = 余弦相似度(一行代码算全部,无需循环)
        qn = qv / (np.linalg.norm(qv) + 1e-9)
        vn = self.vectors / (np.linalg.norm(self.vectors, axis=1, keepdims=True) + 1e-9)
        scores = vn @ qn                              # (N,) 每段与问题的相似度
        idx = np.argsort(-scores)[:top_k]             # 取最高的 top_k 个下标
        return [(self.chunks[i], float(scores[i])) for i in idx]

    def __len__(self) -> int:
        return len(self.chunks)
