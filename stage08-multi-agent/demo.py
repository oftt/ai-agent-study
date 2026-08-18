"""
Stage 8 · 演示:两种多智能体协作
================================
  1. 主从编排(Orchestrator-Worker) —— 动态委派,汇总成调研报告
  2. 内容流水线(Pipeline) —— 研究员→写作者→审稿人→成稿

运行:
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe stage08-multi-agent/demo.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "stage03-react-agent"))

from agent import Tool  # noqa: E402
from orchestrator import Orchestrator, Worker  # noqa: E402
from pipeline import ContentPipeline, make_agents  # noqa: E402


def search_knowledge(query: str) -> str:
    """迷你知识库"""
    kb = {
        "agent": "AI Agent(智能体):能感知环境、自主规划并调用工具完成任务的人工智能系统。核心组件 = LLM + 规划 + 记忆 + 工具。",
        "rag": "RAG(检索增强生成):先检索外部知识库,再让模型基于资料生成回答,显著减少幻觉。",
        "mcp": "MCP(Model Context Protocol):一个开放标准协议,让大模型应用以统一方式连接外部工具和数据源。",
        "multi agent": "多智能体系统:多个各司其职的 Agent 协作,常见模式有主从编排(Orchestrator-Worker)和流水线(Pipeline)。",
        "customer": "智能客服:用 LLM 理解用户意图,结合知识库和工单系统自动回答,常见场景是电商、银行、运营商。",
        "evaluation": "RAG 评估:常用指标有检索质量(Recall/MRR)和生成质量(忠实度/相关性)。",
    }
    for k, v in kb.items():
        if k in query.lower():
            return v
    return f"知识库没有「{query}」相关内容。"


if __name__ == "__main__":
    TOOLS = [Tool("search_knowledge", "在知识库检索关键词并返回知识", search_knowledge)]

    # ========== 1. 主从编排 ==========
    print("#" * 70)
    print("# 演示 1:Orchestrator-Worker 主从编排")
    print("# 任务:调研「智能客服」的应用现状、挑战与前景")
    print("#" * 70)
    workers = [
        Worker("研究员", "你是资料研究员,负责查资料、列事实。", TOOLS),
        Worker("分析师", "你是行业分析师,擅长归纳优势、挑战和趋势。", TOOLS),
        Worker("作家", "你是报告撰写者,擅长把要点组织成通顺的报告。", TOOLS),
    ]
    orch = Orchestrator(workers)
    report = orch.run("调研 AI 智能客服的应用现状、面临的挑战和未来发展前景,写一份简短的调研报告。")
    print("\n\n" + "=" * 70)
    print("📄 最终报告:\n")
    print(report)

    # ========== 2. 内容流水线 ==========
    print("\n\n" + "#" * 70)
    print("# 演示 2:ContentPipeline 内容生产流水线")
    print("# 任务:写一篇关于「AI Agent」的科普短文")
    print("#" * 70)
    researcher, writer, reviewer = make_agents(TOOLS)
    pipeline = ContentPipeline(researcher, writer, reviewer)
    result = pipeline.run("AI Agent")

    print("\n\n" + "=" * 70)
    print(f"🏆 最终成稿:\n")
    print(result["final"])
