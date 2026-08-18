"""
Stage 5 · 数据入库:加载 → 分块 → 向量化 → 存储
=================================================
一个 RAG 系统的"知识沉淀"阶段。一次构建,多次查询。

分块(Chunking)为什么重要:
  - 模型上下文有限,不能把整本手册塞进去
  - 检索是"按片段"找的,片段太大会混入无关内容,太小会丢失语义
  - 重叠(overlap)让相邻片段的信息不因切分而断裂

运行(首次构建索引):
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe stage05-rag/ingest.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # 以便 import lib

from vector_store import PersistentVectorStore  # noqa: E402

DATA_FILE = Path(__file__).resolve().parent / "data" / "员工手册.md"
STORE_DIR = Path(__file__).resolve().parent / "store"


def chunk_text(text: str, chunk_size: int = 250, overlap: int = 40) -> list[str]:
    """
    最简单的定长分块 + 重叠。
    课堂版刻意保持简单(教学优先);真实项目会用语义分块、递归分割等。
    """
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = max(end - overlap, start + 1)   # 下一个块从"上一块尾部 overlap 字"开始
    return chunks


def build_index() -> PersistentVectorStore:
    store = PersistentVectorStore(STORE_DIR)

    # 1. 加载文档
    raw = DATA_FILE.read_text(encoding="utf-8")
    print(f"📄 加载文档: {DATA_FILE.name} ({len(raw)} 字符)")

    # 2. 分块
    chunks = chunk_text(raw)
    print(f"✂️  分块完成: {len(chunks)} 个片段(每段约 250 字,重叠 40 字)")

    # 3. 向量化 + 存储(embedding 要下载模型,已缓存;向量化 60+ 段约需十几秒)
    print("🧮 向量化中...")
    store.add_documents(chunks)
    store.save()
    print(f"💾 已保存到 {STORE_DIR}")

    # 展示前 5 个片段,让你直观感受"分块"长什么样
    print("\n--- 前 5 个片段预览 ---")
    for i, c in enumerate(chunks[:5]):
        print(f"\n[{i}] {c}")
    return store


if __name__ == "__main__":
    build_index()
