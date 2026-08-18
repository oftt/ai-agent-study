# Stage 8 · 多智能体 Multi-Agent

> 日期:2026-08-18 · 状态:✅ 完成 · 源码:`stage08-multi-agent/`(`orchestrator.py` + `pipeline.py` + `demo.py`)

## 🎯 阶段目标

- **主从编排(Orchestrator-Worker)**:一个主 Agent 分工,多个专业 Agent 干活
- **内容流水线(Pipeline)**:固定顺序交接的"团队流水线"
- 体会"专业分工 > 单打独斗":每个 Agent 只做自己最擅长的事

---

## 🧠 两种多智能体模式

```
① 主从编排(Orchestrator-Worker)
   主Agent ──委派──▶ 研究员  ─┐
        │──委派──▶ 分析师   ──┼──▶ 主Agent汇总 → 报告
        └──委派──▶ 作家     ─┘

② 内容流水线(Pipeline)
   研究员 → 写作者 → 审稿人 → 写作者(修改) → 成稿
```

| 维度 | 主从编排 | 流水线 |
|------|---------|--------|
| 任务结构 | 未知 → 主 Agent 动态分配 | 已知 → 固定顺序 |
| 控制方式 | 一个"项目经理"统筹 | 上一步喂给下一步 |
| 类比 | 项目经理带团队 | 工厂流水线 |
| 适合 | 开放式调研/任务 | 内容生产等确定流程 |

核心设计:每个 Agent 是 **独立人格(system)+ 工具 + ReAct 循环** 的组合,通过 `sys.path` 复用 Stage 3 的 `Agent` 类 —— **专业分工 + 复用积木**。

---

## 💻 运行结果(真实)

### 演示 1:主从编排(智能客服调研报告)

委派单(主 Agent 自动生成):
```
- [研究员] 调研应用现状、行业分布、市场规模...
- [分析师] 分析挑战(技术/体验/隐私)与前景...
- [作家]   整合成简短调研报告...
```

**产出**:一份结构完整的调研报告 —— 行业分布与市场规模(约 100-200 亿/年)、技术路线(感知→认知→生成→业务四层)、三大挑战(技术局限/体验痛点/隐私安全)、六条趋势与机遇、以及一个"效率 vs 温度 / 能力 vs 责任"的平衡点表格。

> 🕳️ **真实观察**:知识库里没有"智能客服"相关的词条,worker 多次搜索都返回"没有" → 但 worker 没有卡死,而是**回退到自身知识**继续输出。这说明:工具失败时 Agent 的"弹性"很重要;同时也提醒我们——**工具质量决定多智能体质量**,知识库该建就要建好。

### 演示 2:内容流水线(AI Agent 科普短文)

```
研究员: 查 AI Agent 核心概念(知识库命中 4 要素)
写作者: 写初稿
审稿人: 审核,指出"概念表述不严谨、逻辑因果缺失、偷换概念"等问题
写作者: 按意见修改,并附上"修改要点对照表"
```

**产出**:一篇完成度很高的科普短文("会思考还会动手的智能助手"),结尾的修改对照表清晰展示了 **审稿意见 → 逐条吸收 → 改进了什么** 的闭环。

---

## 🏗️ 代码要点

```python
# orchestrator.py —— 主从编排
class Worker:                       # 专业 Agent = 人格 + 工具
    def __init__(self, name, role, tools):
        self.agent = Agent(system=role)     # 复用 Stage 3
        for t in tools: self.agent.register_tool(t)

class Orchestrator:
    def _assign(self, task):        # ① 主 Agent 委派(JSON)
        ... {"assignments": [{"worker": "研究员", "task": "..."}]} ...
    def run(self, task):
        for a in assigns:
            r = self.workers[a["worker"]].run(a["task"])   # ② 分发执行
        ... 主 Agent 汇总报告 ...                        # ③ 汇总
```

```python
# pipeline.py —— 流水线交接
research = researcher.run(topic)
draft = writer.run(research)      # 上一步输出 → 下一步输入
review = reviewer.run(draft)
final = writer.run(draft, review) # 审稿→修改 = 团队版反思
```

**委派过滤**:主 Agent 可能幻觉出不存在的员工名,`_assign` 里过滤掉不在 `self.workers` 里的名字 —— 多智能体也要有"校验输入"的习惯。

---

## ✍️ 动手练习

1. 给 `demo.py` 加一个"质检员" Worker,让主 Agent 的委派单变成 4 项
2. 把流水线改成 **审稿→修改循环 2 轮**(review → revise → review → revise),对比 1 轮和 2 轮的成稿质量
3. 扩充 `search_knowledge` 的知识库到 20 条,重跑演示 1,观察报告质量提升(验证"工具质量决定智能体质量")
4. 对比思考:什么任务适合编排?什么适合流水线?

## 📌 小结

> **多智能体 = 专业分工 + 团队协作。** 编排模式动态应对开放任务,流水线模式高效处理确定流程,审稿→修改把反思升级成了"团队互评"。
> 下一阶段:工程化与部署 —— 把 Agent 做成能上线服务的产品。
