"""
Stage 8 · 多智能体一:主从编排(Orchestrator-Worker)
====================================================
经典的管理者-员工模式:

  主 Agent(Orchestrator)     → 看任务 → 决定"派谁做、做什么"
  工人 Agent(Worker)         → 各自专业领域,执行被分配的任务
  主 Agent(Orchestrator)     → 收集结果 → 汇总成最终报告

关键设计:
  - 每个 Worker 是一个"专业 Agent" = 独立人格(system)+ 工具 + ReAct 循环
  - Orchestrator 不亲自干活,只做"分工"和"汇总"——像项目经理
  - 委派是动态的:每次根据任务不同,主 Agent 决定用谁

流程:
  ① 主 Agent 读任务 → 输出 JSON 委派单:[{worker, task}, ...]
  ② 把每个子任务发给对应 Worker 执行
  ③ 主 Agent 汇总各 Worker 结果 → 最终报告
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "stage03-react-agent"))

from agent import Agent, Tool  # noqa: E402  复用 Stage 3 的 Agent
from lib.llm import MODEL, get_client  # noqa: E402

client = get_client()


class Worker:
    """一个专业 Agent:独立人格 + 工具 + 执行能力。"""

    def __init__(self, name: str, role: str, tools: list[Tool]):
        self.name = name
        self.agent = Agent(system=role)
        for t in tools:
            self.agent.register_tool(t)

    def run(self, task: str, max_rounds: int = 6) -> str:
        print(f"  └─ [{self.name}] 开始执行: {task[:50]}...")
        return self.agent.run(task, max_rounds=max_rounds)


class Orchestrator:
    def __init__(self, workers: list[Worker]):
        self.workers = {w.name: w for w in workers}
        self.names = list(self.workers.keys())

    def _assign(self, task: str) -> list[dict]:
        """① 主 Agent 读任务,决定派谁做什么。"""
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": (
                    "你是项目经理。把任务拆成 2~4 个子任务,分配给合适的员工。"
                    f"可选员工:{self.names}。只输出 JSON:"
                    "{'assignments': [{'worker': '员工名', 'task': '子任务描述'}]}"
                )},
                {"role": "user", "content": task},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        try:
            assigns = json.loads(resp.choices[0].message.content)["assignments"]
            # 过滤掉不存在的员工名(模型可能幻觉)
            return [a for a in assigns if a.get("worker") in self.workers][:4]
        except (json.JSONDecodeError, KeyError):
            return [{"worker": self.names[0], "task": task}]   # 兜底

    def run(self, task: str) -> str:
        """② 委派 → ③ 执行 → ④ 汇总。"""
        assigns = self._assign(task)
        print(f"\n📋 主 Agent 的委派单({len(assigns)} 项):")
        for a in assigns:
            print(f"   - [{a['worker']}] {a['task'][:44]}...")

        results = []
        for a in assigns:
            worker = self.workers[a["worker"]]
            r = worker.run(a["task"])
            results.append(f"### 员工[{worker.name}] 负责: {a['task']}\n{r}")

        # 汇总:主 Agent 整合成报告
        report = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "你是项目经理,把各员工的产出整合成一份结构清晰、无重复的中文最终报告。"},
                {"role": "user", "content": f"原始任务:{task}\n\n=== 各员工产出 ===\n" + "\n\n".join(results)},
            ],
            temperature=0.3,
        )
        return report.choices[0].message.content
