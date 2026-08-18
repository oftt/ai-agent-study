"""
Stage 6 · 综合演示:混合检索 + 元数据过滤 + LLM 重排
======================================================
三个能力依次展示:
  1. 混合检索 vs 纯向量 —— 看 RRF 融合把两路优势合并
  2. 元数据过滤 —— 只在一章里检索(比如只在"报销制度"里找)
  3. LLM 重排 —— 模型从候选里挑最相关的

运行:
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe stage06-rag-advanced/demo.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hybrid_store import HybridStore, STORE_DIR  # noqa: E402
from lib.llm import MODEL, get_client  # noqa: E402

client = get_client()


def show(name: str, items: list, width: int = 34):
    print(f"\n  【{name}】")
    for i, (idx, s) in enumerate(items, 1):
        first_line = store.chunks[idx].split("\n")[0][:width]
        print(f"    #{i} 章节「{store.metas[idx]}」| {first_line}... | score={s:.3f}")


if __name__ == "__main__":
    if not (STORE_DIR / "vectors.npy").exists():
        print("首次运行,构建索引...")
        store = HybridStore().build()
    else:
        store = HybridStore.load()
    print(f"📚 索引:{len(store)} 个片段,章节:{sorted(set(store.metas))}")

    # ========== 1. 混合检索 vs 纯向量 ==========
    print("\n" + "=" * 70)
    print("① 混合检索 vs 纯向量 —— 查询含精确术语:「OA 系统」")
    print("=" * 70)
    q = "员工出差用 OA 系统报备,这个 OA 系统是什么?"
    show("纯向量 top4", store.vector_search(q, 4))
    show("混合检索 top4", store.hybrid_search(q, 4))

    # ========== 2. 元数据过滤 ==========
    print("\n" + "=" * 70)
    print("② 元数据过滤 —— 只在「报销制度」章节里检索:「住宿标准」")
    print("=" * 70)
    all_ids = [i for i, _ in store.hybrid_search("住宿标准是多少", 8)]
    filtered = store.filter_by_meta(all_ids, "报销")
    print(f"混合检索召回 {len(all_ids)} 个,按章节过滤后剩 {len(filtered)} 个(都是报销章节):")
    for i in filtered:
        print(f"  - 「{store.metas[i]}」{store.chunks[i][:40]}...")

    # ========== 3. LLM 重排 ==========
    print("\n" + "=" * 70)
    print("③ LLM 重排 —— 候选 5 个,让模型挑最相关的 3 个:「年假能休几天」")
    print("=" * 70)
    cand = [i for i, _ in store.hybrid_search("年假能休几天", 5)]
    print("重排前的候选顺序:")
    for i in cand:
        print(f"  - 「{store.metas[i]}」{store.chunks[i][:36]}...")
    reranked = store.llm_rerank("年假能休几天", cand, top_k=3)
    print("\nLLM 重排后(只留最相关的 3 个):")
    for i in reranked[:3]:
        print(f"  - 「{store.metas[i]}」{store.chunks[i][:36]}...")
