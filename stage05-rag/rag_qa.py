"""
Stage 5 · 检索增强生成(RAG)问答
================================
核心流程 retrieve → augment → generate,三步:
  1. RETRIEVE  把问题向量化,从向量库检索最相关的 top_k 个片段
  2. AUGMENT   把检索到的片段拼进提示词作为"参考资料"
  3. GENERATE  让模型基于参考资料回答(不许凭空发挥)

运行(需要先跑 ingest.py 建好索引):
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe stage05-rag/rag_qa.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # 以便 import lib

from lib.llm import MODEL, get_client  # noqa: E402
from vector_store import PersistentVectorStore  # noqa: E402

client = get_client()
STORE_DIR = Path(__file__).resolve().parent / "store"


def rag_ask(question: str, store: PersistentVectorStore, top_k: int = 3) -> tuple[str, list]:
    """RAG 三件套:检索 → 增强 → 生成。返回 (回答, 检索到的片段)。"""
    # ---- RETRIEVE ----
    hits = store.search(question, top_k=top_k)

    # ---- AUGMENT ----
    context = "\n\n".join(f"[片段{i+1}] {text}" for i, (text, _) in enumerate(hits))
    prompt = (
        "你是员工手册问答助手。请严格依据下面的资料回答问题。\n"
        "规则:资料里没有的内容,直接回答「资料里没有提到」。不要编造。\n\n"
        f"===== 资料 =====\n{context}\n\n"
        f"===== 问题 =====\n{question}"
    )

    # ---- GENERATE ----
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "你是知识库问答助手,回答简洁准确。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,   # RAG 回答用低温,求准不求创意
    )
    return resp.choices[0].message.content, hits


if __name__ == "__main__":
    if not (STORE_DIR / "vectors.npy").exists():
        print("⚠️  尚未建索引,请先运行: python stage05-rag/ingest.py")
        sys.exit(1)

    store = PersistentVectorStore.load(STORE_DIR)
    print(f"📚 加载向量库: {len(store)} 个片段\n")

    questions = [
        "正式员工每年有几天的带薪年假?",
        "出差住宿的标准是多少?",
        "考勤迟到会怎么处理?",
        "晋升需要满足哪些条件?",
        "公司楼下的咖啡店叫什么名字?",   # 知识库里没有 → 考验"不乱编"
    ]

    for q in questions:
        print("=" * 60)
        print(f"问: {q}")
        answer, hits = rag_ask(q, store)
        print("\n🔍 检索到的片段(可追溯性:让答案有据可查):")
        for i, (text, score) in enumerate(hits, 1):
            print(f"  [{score:.2f}] {text[:80]}...")
        print(f"\n🤖 回答: {answer}\n")
