"""
毕业项目 · 单元测试
====================
覆盖:分块、知识库检索、Agent 记忆、工具安全、用量统计。
除知识库检索外,其余测试不调真实 LLM。

运行:
  cd stage10-final
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe -m pytest test_final.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest  # noqa: E402

from knowledge_base import KnowledgeBase, STORE_DIR, fixed_chunk, section_chunk  # noqa: E402
from agent import FinalAgent, calculate  # noqa: E402
from usage import UsageTracker  # noqa: E402


# ---------- 分块 ----------

def test_fixed_chunk_with_overlap():
    text = "x" * 100
    chunks = fixed_chunk(text, size=30, overlap=10)
    assert len(chunks) >= 4
    assert chunks[0] == "x" * 30
    assert "x" * 10 in chunks[1][:10]      # 第二块开头是上一块的尾巴(重叠)


def test_section_chunk_keeps_meta():
    text = "## 一、工具调用\n内容A。\n## 二、ReAct\n内容B。"
    chunks, metas = section_chunk(text, chunk_size=200, overlap=10)
    assert len(chunks) == 2
    assert metas[0] == "一、工具调用"
    assert metas[1] == "二、ReAct"


# ---------- 工具安全 ----------

def test_calculate_whitelist():
    assert calculate("(12+5)*3") == "51"
    assert "非法" in calculate("1; rm -rf /")     # 注入被拒


# ---------- Agent 记忆 ----------

def test_agent_memory_trim():
    agent = FinalAgent(kbase=None, max_memory=6)  # 只用记忆能力,不需要知识库
    msgs = [{"role": "system", "content": "s"}] + [{"role": "user", "content": str(i)} for i in range(20)]
    agent._trim(msgs)
    assert len(msgs) == 7
    assert msgs[-1]["content"] == "19"


# ---------- 知识库检索 ----------

@pytest.fixture(scope="module")
def kb():
    if (STORE_DIR / "vectors.npy").exists():
        return KnowledgeBase.load()
    return KnowledgeBase().build()


def test_kb_search_relevant(kb):
    hits = kb.hybrid_search("ReAct 的循环包括哪几步?", top_k=3)
    assert len(hits) >= 1
    # 命中内容应包含"循环"或"ReAct"等关键词
    top_text = kb.chunks[hits[0][0]]
    assert any(k in top_text for k in ["循环", "ReAct", "思考"])


def test_search_knowledge_formatted(kb):
    out = kb.search_knowledge("RAG 为什么能减少幻觉")
    assert "知识库" in out or "RAG" in out or "幻觉" in out
    assert "·" in out                              # 带"文件名·章节"元数据


# ---------- 用量 ----------

def test_usage_roundtrip():
    u = UsageTracker(log_file="_final_test_usage.json")
    u.add(1000, 500)
    assert u.total_prompt == 1000
    assert u.cost() > 0
    assert "累计调用" in u.summary()
    u.log_file.unlink(missing_ok=True)
