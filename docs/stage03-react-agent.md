# Stage 3 · Agent 核心循环(ReAct)⭐ 里程碑

> 日期:2026-08-18 · 状态:✅ 完成 · 源码:`stage03-react-agent/`(`agent.py` + `demo.py`)

## 🎯 阶段目标

- 掌握 ReAct(推理 + 行动)设计模式
- 把 Stage 2 的工具调用封装成**可复用的 Agent 框架**
- 具备多工具协作、错误自救、防死循环三个健壮性能力

**这是第一个真正意义上的 Agent**:它自己规划、自己调工具、自己根据结果调整,直到完成任务。

---

## 🧠 ReAct 模式:Agent 的"思维方式"

ReAct = **Re**asoning(推理)+ **Act**ing(行动)。模型不再是"问一句答一句",而是循环:

```
Thought(想)    "需要查天气才能回答"
  ↓
Act(做)        调用 get_weather("北京")
  ↓
Observation(看)  ← 晴天,25°C
  ↓
Thought(想)    "知道了,组织回答"
  ↓
Answer(答)     最终回答
```

**观察结果会进入下一轮思考**,这正是"智能体"的核心:它不是一次性生成,而是**边做边看边想**。

---

## 🏗️ 框架架构(`agent.py`)

### `Tool` 类 —— 给模型一个"可调用的手"

```python
@dataclass
class Tool:
    name: str          # 工具名
    description: str   # 给模型的说明
    func: Callable     # 真正的 Python 函数
    parameters: dict = None   # 不填则自动生成
```

**亮点:`_auto_parameters()`** —— 利用 `inspect.signature` 读取函数签名,自动生成 JSON Schema:

```python
def multiply(a: int, b: int) -> int:   # 只写类型注解
    return a * b

# 自动生成:
# {"type":"object", "properties":{"a":{"type":"integer"}, "b":{"type":"integer"}},
#  "required":["a","b"]}
```

以后注册工具**零样板代码**。这就是"把重复劳动交给代码"的思想。

### `Agent` 类 —— 循环 + 注册表 + 兜底

```python
class Agent:
    def register_tool(self, tool): ...      # 工具注册表
    def run(self, user_input, max_rounds=8): # ReAct 主循环
```

`run()` 里的循环就是 Stage 2 的循环,但多了三个健壮性设计:

### 健壮性 1:错误兜底(工具挂了自己能救)

```python
def execute(self, **kwargs) -> str:
    try:
        return str(self.func(**kwargs))
    except Exception as e:
        return f"工具执行出错: {type(e).__name__}: {e}"   # ← 不崩溃,变成"观察"喂回
```

工具抛异常不再让程序崩溃,而是变成一条"观察",模型看到后能自行调整(比如解释"除以零无定义")。

### 健壮性 2:未知工具名

```python
observation = (
    f"没有名为「{name}」的工具,请使用已注册的工具"
    if tool is None else tool.execute(**args)
)
```

模型偶尔会幻觉出不存在的工具 → 明确告诉它"换一个"。

### 健壮性 3:最大迭代上限

`max_rounds=8` 硬顶住循环,防止模型反复调工具不收敛(既防死循环,也防烧钱)。

---

## 💻 运行结果

### 任务 1:多工具协作

```
🔄 第 1 轮:模型请求调用 3 个工具
   ▶ 行动: multiply({'a': 1234, 'b': 5678})      ← 观察: 7006652
   ▶ 行动: get_current_time({})                   ← 观察: 2026-08-18 22:01:52 (Tuesday)
   ▶ 行动: search_knowledge({'query': 'RAG'})     ← 观察: RAG(检索增强生成)...
🤖 最终回答: 1234×5678=7006652 ✅ | 今天是2026年8月18日,星期二 | RAG 介绍...
```

**一轮并行 3 个工具,拿到数据后组织成结构化回答。**

### 任务 2:错误自救

```
🔄 第 1 轮:模型请求调用 1 个工具
   ▶ 行动: divide({'a': 5, 'b': 0})
   ← 观察: 工具执行出错: ZeroDivisionError: division by zero
🤖 最终回答: 5 ÷ 0 在数学上是无定义的……(从数学定义/极限/编程角度完整解释)
```

**工具报错 → Agent 不崩 → 还能把错误讲得明明白白。**这就是"观察驱动思考"的威力。

---

## 📌 现在的你已经掌握

```
Stage 0  环境 + 调用        →  能和大模型说话
Stage 1  参数/流式/结构化    →  能控制输出
Stage 2  工具调用            →  模型能指挥你执行
Stage 3  ReAct 循环          →  ★ 你的第一个 Agent:规划、执行、观察、纠错
```

从 Stage 4 开始,我们把 Agent 变"聪明":记忆、RAG、多 Agent、工程化。

---

## ✍️ 动手练习

1. 在 `demo.py` 里加一个新工具(比如 `word_count(text)` 统计字数),注册后问"数一下'人工智能'四个字有几笔"(它会先查知识再算)
2. 把 `max_rounds` 改成 1,问一个需要两步的任务,观察强制截断效果
3. 故意问一个工具都答不上的问题,看 Agent 如何"承认自己查不到"

## 🕳️ 踩坑记录

| 坑 | 解法 |
|----|------|
| 工具函数忘了写类型注解 → 参数 Schema 空 | `_auto_parameters` 依赖注解,注册前检查 |
| 工具抛异常导致程序崩溃 | `execute()` 里 try/except 转成字符串观察 |
| 模型幻觉出不存在的工具名 | 返回"没有此工具"明确纠正 |
| 无限循环 | `max_rounds` 硬上限 |
