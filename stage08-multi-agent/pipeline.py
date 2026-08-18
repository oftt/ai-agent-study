"""
Stage 8 · 多智能体二:内容生产流水线(固定交接)
================================================
另一种多智能体模式:像工厂流水线一样,**上一步的输出交给下一步**。

  研究员 → 写作者 → 审稿人 → (写作者修改) → 成稿

对比主从编排:
  编排(Orchestrator-Worker)  —— 主 Agent 动态分配,适合"任务结构未知"
  流水线(Pipeline)           —— 固定顺序交接,适合"流程确定的流水作业"

关键设计:
  - 每个环节是一个专业 Agent(研究员查资料 / 写作者行文 / 审稿人挑刺)
  - 交接 = 把上一步的完整输出,作为下一步的输入
  - 审稿 → 修改形成一个小反思循环(把 Stage 7 的反思做成"团队版")
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "stage03-react-agent"))

from agent import Agent, Tool  # noqa: E402


class ContentPipeline:
    def __init__(self, researcher, writer, reviewer):
        self.researcher = researcher   # 三个都是 Worker 或 Agent
        self.writer = writer
        self.reviewer = reviewer

    def run(self, topic: str) -> dict:
        """执行流水线,返回各环节产出,方便观察。"""
        print(f"\n📚 [研究员] 搜集资料...")
        research = self.researcher.run(
            f"搜集与「{topic}」相关的核心知识点,用简洁条目列出,供写作使用。", max_rounds=4
        )

        print(f"\n✍️  [写作者] 撰写初稿...")
        draft = self.writer.run(
            f"基于下面的资料,写一篇约 300 字的科普短文,主题:{topic}。\n\n=== 资料 ===\n{research}",
            max_rounds=4,
        )

        print(f"\n🔍 [审稿人] 审核初稿...")
        review = self.reviewer.run(
            f"请审阅下面的文章,指出:事实性错误、逻辑问题、表述冗余,并给出具体修改建议。\n\n=== 文章 ===\n{draft}",
            max_rounds=2,
        )

        print(f"\n🔄 [写作者] 按意见修改...")
        final = self.writer.run(
            f"根据审稿意见修改下面的文章,输出最终版。\n\n=== 原稿 ===\n{draft}\n\n=== 审稿意见 ===\n{review}",
            max_rounds=2,
        )

        return {"research": research, "draft": draft, "review": review, "final": final}


def make_agents(tools: list[Tool]) -> tuple[Agent, Agent, Agent]:
    """创建研究员 / 写作者 / 审稿人三个专业 Agent。"""
    researcher = Agent(system="你是资料研究员,擅长查找并提炼事实。只输出可靠的要点,不确定的标注出来。")
    writer = Agent(system="你是科普作家,文笔流畅,能把技术概念讲得通俗易懂。")
    reviewer = Agent(system="你是严格的主编,负责挑毛病:事实错误、逻辑漏洞、表述啰嗦,并给具体修改建议。")
    for a in (researcher, writer, reviewer):
        for t in tools:
            a.register_tool(t)
    return researcher, writer, reviewer
