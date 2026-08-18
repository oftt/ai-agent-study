"""
Stage 6 · RAG 检索质量评估
==========================
用数据说话:混合检索到底比纯向量好多少?

评估指标(检索侧):
  - Recall@k   正确答案所在的片段,是否出现在前 k 名(越高越好)
  - MRR        正确答案排名的倒数平均值;第 1 名=1.0,第 2 名=0.5...(越接近 1 越好)

方法:准备一组「问题 → 答案特征词」,自动定位黄金片段(gold),
再分别用纯向量 / 混合检索跑,统计指标对比。

运行:
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe stage06-rag-advanced/evaluate.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hybrid_store import HybridStore, STORE_DIR  # noqa: E402


def gold_index(store: HybridStore, snippet: str):
    """找到包含特征词的片段下标(即"标准答案应该在的片段")。"""
    for i, c in enumerate(store.chunks):
        if snippet in c:
            return i
    return None


def recall_at_k(ranked_ids, gold, k=3):
    return 1.0 if gold in ranked_ids[:k] else 0.0


def mrr(ranked_ids, gold):
    try:
        return 1.0 / (ranked_ids.index(gold) + 1)
    except ValueError:
        return 0.0


# 评估集:问题 + 答案特征词(出现在手册原文里)
EVAL_SET = [
    {"question": "正式员工带薪年假几天?", "snippet": "10 天带薪年假"},
    {"question": "出差一线城市住宿每晚多少钱?", "snippet": "500 元"},
    {"question": "迟到多久按半天事假处理?", "snippet": "30 分钟"},
    {"question": "晋升评审一年进行几次?", "snippet": "3 月和 9 月"},
    {"question": "离职后保密义务持续几年?", "snippet": "2 年"},
    {"question": "出差餐饮补贴每天多少钱?", "snippet": "120 元"},
    {"question": "事假每年上限几天?", "snippet": "10 天"},
]


def run_retrieval(store, method: str):
    """返回每个问题的 (gold 是否进前3, MRR)"""
    rec, mrrs = [], []
    for item in EVAL_SET:
        q = item["question"]
        ranked = [i for i, _ in (
            store.vector_search(q, 5) if method == "vector" else store.hybrid_search(q, 5)
        )]
        gold = gold_index(store, item["snippet"])
        rec.append(recall_at_k(ranked, gold, 3))
        mrrs.append(mrr(ranked, gold))
    return rec, mrrs


if __name__ == "__main__":
    if not (STORE_DIR / "vectors.npy").exists():
        store = HybridStore().build()
    else:
        store = HybridStore.load()
    print(f"📚 索引:{len(store)} 个片段\n")
    print(f"{'方法':<8}{'Recall@3':<12}{'MRR':<8}")
    print("-" * 30)

    for method, label in [("vector", "纯向量"), ("hybrid", "混合RRF")]:
        rec, mrrs = run_retrieval(store, method)
        r3 = sum(rec) / len(rec)
        m = sum(mrrs) / len(mrrs)
        print(f"{label:<8}{r3:<12.2f}{m:<8.2f}")

    print("\n说明:Recall@3 = 正确答案在 top3 的比例;MRR = 正确答案排名的倒数均值。")
    print("如果混合检索两项都更高,说明 RRF 融合有效 —— 用数据证明了改进。")
