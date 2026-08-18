# Stage 7 · 复杂 Agent 与规划

> 日期:2026-08-18 · 状态:✅ 完成 · 源码:`stage07-planning/`(`planner.py` + `reflect.py` + `demo.py`)

## 🎯 阶段目标

- **Plan-and-Execute**:复杂任务先规划、再逐步执行
- **Reflection**:Agent 自我评审、自我改进
- 复用了 Stage 3 的迷你 Agent 作为"执行器"——**站在自己之前代码的肩膀上**

---

## 🧠 两种高级模式

### 1. Plan-and-Execute(先规划后执行)

| | ReAct(Stage 3) | Plan-and-Execute(本阶段) |
|---|---|---|
| 思路 | 边想边做,走一步看一步 | 先整体规划,再逐步执行 |
| 适合 | 交互式、开放、走一步才知道下一步 | 结构化、长任务、可预知步骤 |
| 优势 | 灵活 | 步骤清晰可追踪、上下文聚焦 |

流程:
```
① PLAN    模型拆解任务 → JSON 步骤列表(复用 Stage 1 结构化输出)
② EXECUTE 每步交给 Stage 3 的 Agent(带工具)执行
③ 汇总    各步结果整合成最终报告
```

### 2. Reflection(反思循环)

```
Generate(生成) → Critique(评审) → Revise(重写) → 再评审... → 定稿
```

把"评价"和"写作"拆成两个独立角色,各自专注。模型的自我批评往往比一次成稿写得好。

---

## 💻 运行结果(真实)

### 演示 1:规划 3 周 AI Agent 学习计划

- **规划**:5 个子步骤(整体框架 / 每周详细设计 / ReAct 知识整合)
- **执行**:每步都调用了 `search_knowledge` 工具查资料
- **汇总**:产出一份结构完整的计划 —— 含三周每日安排表、每周验收清单、ReAct 知识专题、时间投入概览、终极验收清单

> 🕳️ **真实观察**:其中一个子任务触发了 `(达到最大迭代次数,未得到最终回答)` —— 模型反复调工具没有收尾,被 `max_rounds` 兜住。这正是 Stage 3 设计的**防死循环**在真实场景发挥了作用;汇总器依然能基于其他步骤整合出报告。

### 演示 2:咖啡店宣传文案(2 轮反思)

**初稿**:`美式无糖,苦得理直气壮。别加糖,别加奶,别加滤镜——……(此处应有气泡音:)无糖美式,纯爷们儿/纯姐们儿的液体bra`

**评审(第 1 轮)一针见血**:
1. "黑眼圈是勋章"逻辑不通(咖啡是提神的,不是缺觉的原因)
2. "清醒是借来的但不用还"自相矛盾(咖啡因代谢后清醒必然消失)
3. "液体bra"低俗、偏离品牌格调,建议换成"续命水""苦味能量弹"
4. "(此处应有气泡音:)"是舞台提示不是文案
5. "别加滤镜"为押韵凑数,与卖点无关 → 建议改"别加借口"

**重写 2 轮后最终稿**(融合"硬汉"意象 + 口感细节):
```
深烘的豆子练过,焦香够硬,像一拳打进喉底。
冰球撞进去,苦味炸开,三秒后回甘从舌根偷渡。
这杯苦,是今天唯一敢当面顶撞你的东西。
```

**提升肉眼可见**:逻辑自洽、意象统一、有了可感知的细节。这就是反思的价值。

---

## 🏗️ 代码要点

```python
# planner.py —— 规划器与执行器解耦
class PlanExecuteAgent:
    def plan(self, task) -> list[dict]:      # 拆解 → JSON
        ...  response_format={"type": "json_object"} ...
    def run(self, task) -> str:
        for s in steps:
            r = self.executor.run(s["detail"])   # 复用 Stage 3 的 Agent 执行
        ... 汇总器整合报告 ...
```

```python
# reflect.py —— 三个小函数循环
draft = generate(question)
for i in range(rounds):
    feedback = critique(question, draft)   # 扮演"挑剔评审"
    draft = revise(question, draft, feedback)  # 根据意见重写
```

复用方式:两个脚本都 `sys.path.insert` 指向 `stage03-react-agent/`,直接 `from agent import Agent, Tool`。**这就是模块化工程——之前的积累变成现在的零件。**

---

## ✍️ 动手练习

1. 把 `reflect.py` 的 `rounds` 从 2 改成 4,观察第 3、4 轮改进是否还明显(会发现边际效益递减——这也是真实规律)
2. 给 `planner.py` 的任务换成"为公司做一份新品发布会方案",看规划是否合理
3. 在 plan 提示词里要求"步骤间有依赖关系",观察执行器如何处理
4. 对比:同一任务用 ReAct(Stage 3)和 Plan-Execute 各跑一次,体会两者差异

## 📌 小结

> **规划让 Agent 有条理,反思让 Agent 有品质。** 这两个模式是 Agent"从能用变好用"的关键一跃。
> 下一阶段:多智能体协作 —— 让多个各司其职的 Agent 组成"团队"。
