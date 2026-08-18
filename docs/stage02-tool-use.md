# Stage 2 · 工具调用 Tool Use

> 日期:2026-08-18 · 状态:✅ 完成 · 源码:`stage02-tool-use/`

## 🎯 阶段目标

- 理解工具调用(function calling)的完整流程
- 看清模型返回的"调用指令"长什么样
- 写出完整的工具调用循环(执行 → 回填 → 再问),得到最终答案

**这一步是关键一跃**:之前模型只会"说",现在它能"指挥你做事"。模型说出意图,程序负责执行——这正是 Agent 的雏形。

---

## 🧠 核心概念:工具调用的 4 步

```
你定义工具(给模型的"说明书")     →  tools 参数,JSON Schema 描述函数
   ↓
模型决定调用                     →  response 里出现 tool_calls(finish_reason=tool_calls)
   ↓
你执行工具(真去查天气/算数)       →  Python 函数
   ↓
结果回填给模型                   →  role="tool" 消息 + tool_call_id
   ↓
模型基于结果给出最终回答           →  loop,直到没有 tool_calls
```

**关键认知**:模型本身**不会真的执行任何东西**。它只是"表达调用意图",执行权永远在你手里。这保证了安全性——你可以审查、限制它调用什么。

### 工具说明书长什么样

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",                       # 函数名(程序用来匹配)
        "description": "查询指定城市的当前天气",      # 告诉模型这工具干嘛的
        "parameters": {                               # 参数 Schema:要什么参数
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
}]
```

> 💡 `description` 写得好不好,直接决定模型会不会用、用得对不对。这是"提示词工程"在工具上的体现。

### 模型返回的调用指令

```python
msg.tool_calls[0].function.name        # "get_weather"
msg.tool_calls[0].function.arguments   # '{"city": "北京"}' —— 是 JSON 字符串!
```

🕳️ **坑:arguments 是字符串**,要 `json.loads()` 才能变成 dict。

### 回填工具结果的格式(最容易踩坑)

```python
messages.append(msg)          # ① 先把模型的"调用指令"整体存入历史(它带 tool_calls 字段)
messages.append({
    "role": "tool",            # ② 工具结果用 role="tool"
    "tool_call_id": call.id,   # ③ 必须带上对应指令的 id —— 模型据此对齐"哪个工具返回了什么"
    "content": str(result),
})
```

🕳️ **坑:忘了 `tool_call_id` 或顺序不对,API 会直接报错。**

---

## 💻 代码讲解

### `01_first_tool_call.py` —— 只看不执行

只发请求、观察模型返回的 tool_calls,理解"模型想调谁、带什么参数"。

### 运行结果

```
finish_reason: tool_calls
调用 #1   要调用的工具名: get_weather   参数: {'city': '北京'}
调用 #2   要调用的工具名: get_current_time   参数: {}
```

模型一次请求了两个工具——证明它能**并行规划**。

### `02_tool_loop.py` —— 完整循环

核心是 `run_with_tools()` 里的循环:

```python
for round_no in range(max_rounds):          # max_rounds 防死循环
    resp = client.chat.completions.create(..., tools=TOOLS_SCHEMA, ...)
    if not msg.tool_calls:                  # 没有工具调用 → 最终答案
        return msg.content
    messages.append(msg)                    # 存指令
    for call in msg.tool_calls:
        result = TOOLS_IMPL[name](**args)   # 按名字找到函数并执行
        messages.append({"role": "tool", "tool_call_id": call.id, "content": str(result)})
```

### 运行结果

```
🔄 第 1 轮:模型请求调用 2 个工具
   ▶ 执行 get_weather({'city': '北京'})
     ← 结果: 晴,25°C
   ▶ 执行 get_current_time({})
     ← 结果: 2026-08-18 22:00:44
🤖 最终回答: 北京现在是晴天,晚上气温25°C,体感比较舒适……
```

模型先调工具拿数据,再基于**真实结果**组织回答。**这就是"接地气"的对话**——不会瞎编天气。

---

## 🕳️ 踩坑记录

| 坑 | 现象 | 解法 |
|----|------|------|
| arguments 是字符串 | `{"city": "北京"}` 是 str | `json.loads()` 转 dict |
| 忘了 `tool_call_id` | API 报错 tool_call_id 不匹配 | 回填时带上对应 `call.id` |
| 历史里存错指令 | 报"assistant message with tool_calls must not have content"之类 | 原样 `messages.append(msg)` |
| 模型反复调工具 | 死循环,烧钱 | `max_rounds` 硬上限 |

---

## ✍️ 动手练习

1. 在 `02_tool_loop.py` 里**新增一个工具**:`multiply(a, b)` 返回两数相乘,并把 schema 和实现加进注册表,然后问"帮我算 12×7 是多少"
2. 把 `max_rounds` 改成 `1`,看模型调完工具后强制结束会发生什么
3. 把天气数据 `fake` 换成 `None` 的 city,观察模型如何应对"工具查不到"

## 📌 小结

> **工具调用 = 模型做决策,程序做执行,结果回填再决策。** 
> 你已经手握构建 Agent 的最后一个核心零件。下一阶段把它打磨成正式的 Agent 框架:工具注册表、循环、错误处理、迭代上限,一应俱全。
