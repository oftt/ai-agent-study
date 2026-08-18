"""
Stage 7 · Plan-and-Execute 规划型 Agent
=========================================
相比 Stage 3 的"边想边做"(ReAct),复杂任务更适合**先规划再执行**:

  ReAct:        边思考边调用工具,走一步看一步(适合交互式/开放任务)
  Plan-Execute: 先让模型把大任务拆成有序步骤,再逐步执行(适合结构化/长任务)

流程:
  1. PLAN    模型拆解任务 → 输出结构化步骤列表(JSON,复用 Stage 1 的套路)
  2. EXECUTE 每一步交给 Stage 3 的迷你 Agent(带工具)去执行
  3. 汇总    把各步结果整合成最终报告

好处:步骤清晰可追踪、中途可调整、每个子任务上下文更聚焦。
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))                       # 以便 import lib
sys.path.insert(0, str(ROOT / "stage03-react-agent"))  # 以便复用 Stage 3 的 agent.py

from agent import Agent, Tool  # noqa: E402  复用 Stage 3 的迷你 Agent
from lib.llm import MODEL, get_client  # noqa: E402

client = get_client()


class PlanExecuteAgent:
    def __init__(self, tools: list[Tool], system: str = "你是执行助手,一步步完成子任务,用中文回答。"):
        self.executor = Agent(system=system)   # 复用 Stage 3 的 Agent 作为"执行器"
        for t in tools:
            self.executor.register_tool(t)

    def plan(self, task: str) -> list[dict]:
        """① PLAN:让模型把任务拆成有序步骤,输出结构化 JSON。"""
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": (
                    "你是任务规划师。把用户任务拆解成 3~5 个可独立执行的子步骤,"
                    "只输出 JSON:{'steps': [{'step': '步骤标题', 'detail': '具体要做什么'}]}"
                )},
                {"role": "user", "content": task},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        try:
            return json.loads(resp.choices[0].message.content).get("steps", [])
        except json.JSONDecodeError:
            return [{"step": "执行", "detail": task}]   # 解析失败兜底:当单个任务做

    def run(self, task: str, max_steps: int = 5) -> str:
        """Plan → Execute → 汇总。"""
        steps = self.plan(task)[:max_steps]
        print(f"\n📋 规划出 {len(steps)} 个子步骤:")
        for i, s in enumerate(steps, 1):
            print(f"   {i}. {s['step']} —— {s['detail'][:40]}")

        results = []
        for i, s in enumerate(steps, 1):
            print(f"\n▶ 执行子任务 {i}/{len(steps)}: {s['step']}")
            # 每个子任务用 Stage 3 的 ReAct 循环跑(可调用工具)
            r = self.executor.run(s["detail"], max_rounds=4)
            print(f"   ✔ 子任务结果: {r[:100]}...")
            results.append(f"### {i}. {s['step']}\n{r}")

        # 汇总:把各步结果整合成一份完整报告
        report = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "你是报告整合器,把子任务结果整合成一份结构清晰、连贯的中文最终报告。"},
                {"role": "user", "content": f"原始任务:{task}\n\n=== 子任务结果 ===\n" + "\n\n".join(results)},
            ],
            temperature=0.3,
        )
        return report.choices[0].message.content
