"""
Stage 7 · 演示:规划型 Agent + 反思
==================================
两个演示:
  1. Plan-and-Execute —— 制定 3 周 AI Agent 学习计划(规划 + 查知识库工具)
  2. Reflection —— 咖啡店宣传文案(生成 → 评审 → 重写)

运行:
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe stage07-planning/demo.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "stage03-react-agent"))

from agent import Tool  # noqa: E402
from planner import PlanExecuteAgent  # noqa: E402
from reflect import reflect  # noqa: E402


def search_knowledge(query: str) -> str:
    """迷你知识库(模拟联网搜索)"""
    kb = {
        "react": "ReAct:模型交替进行 推理(Reasoning)与 行动(Acting)的 Agent 设计模式,先想再做再观察。",
        "rag": "RAG(检索增强生成):先检索外部知识库,再让模型基于资料生成回答,减少幻觉。",
        "multi agent": "多智能体:多个各司其职的 Agent 协作,比如研究员负责搜集、写作者负责成稿、审稿人负责把关。",
        "plan": "Plan-and-Execute:先规划步骤再逐步执行的任务分解模式,适合复杂长任务。",
        "prompt": "提示词工程:通过精心设计 system 提示词引导模型行为,是成本最低的调优手段。",
    }
    for k, v in kb.items():
        if k in query.lower():
            return v
    return f"知识库没有「{query}」相关内容。"


if __name__ == "__main__":
    # ========== 1. Plan-and-Execute ==========
    print("#" * 70)
    print("# 演示 1:Plan-and-Execute 规划型 Agent")
    print("# 任务:为编程新手制定 3 周 AI Agent 学习计划,并解释 ReAct")
    print("#" * 70)
    tools = [Tool("search_knowledge", "在知识库检索关键词并返回知识", search_knowledge)]
    agent = PlanExecuteAgent(tools)
    task = (
        "为完全不懂 AI 的编程新手,制定一份 3 周(每周 5 天)的 AI Agent 入门学习计划。"
        "每个阶段要列出:学习主题、每天大致安排、期望成果。"
        "最后用知识库解释一下 ReAct 模式并写进计划。"
    )
    report = agent.run(task)
    print("\n\n" + "=" * 70)
    print("📄 最终报告:\n")
    print(report)

    # ========== 2. Reflection ==========
    print("\n\n" + "#" * 70)
    print("# 演示 2:Reflection 反思模式")
    print("# 任务:写咖啡店宣传文案(生成→评审→重写 2 轮)")
    print("#" * 70)
    final = reflect("为一家主打「无糖美式」的咖啡店写一段 120 字左右的宣传文案,要有趣、有记忆点。", rounds=2)
    print("\n\n🏆 最终稿:\n")
    print(final)
