# Stage 1 · 基础 API 调用

> 日期:2026-08-18 · 状态:✅ 完成 · 源码:`stage01-basic-api/`

## 🎯 阶段目标

- 多轮对话:让模型"记住"上下文
- 亲手感受 `temperature` / `max_tokens` / `top_p` / `seed` 参数
- 流式输出:打字机效果
- 结构化输出:模型返回严格可校验的 JSON

**这四样都是 Agent 的必备地基**:多轮对话 = Agent 对话界面的基础;参数 = 调优手段;流式 = 交互体验;结构化输出 = 通往工具调用的桥梁。

---

## 1️⃣ 多轮对话(`01_multi_turn.py`)

### 原理

大模型是**无状态**的——它不记得你上一句说了什么。所谓"记忆",全靠**每次把完整对话历史一起发过去**。

```
第 1 轮:  [system] + [user:你是谁?]                              → 模型回答A
第 2 轮:  [system] + [user:你是谁?] + [assistant:A] + [user:你会翻筋斗云吗?] → 回答B
第 3 轮:  [system] + [user:你是谁?] + [assistant:A] + [user:...] + [assistant:B] + [user:...]
```

**核心代码**(就两行追加):

```python
messages.append({"role": "user", "content": user_text})          # 1. 存用户提问
...
reply = response.choices[0].message.content
messages.append({"role": "assistant", "content": reply})          # 2. 存模型回答
```

### 运行结果

```
你:你是谁?
悟空: 俺老孙是齐天大圣孙悟空！不过……如今也就是只被压过五百年的猴子，嘿嘿。

你:那你会翻筋斗云吗?
悟空: 会啊！俺老孙一个筋斗就是十万八千里！不过……现在老了，翻完还得歇会儿，嘿嘿。

你:我刚才问你,你自己说你是什么来着?
悟空: 嘿嘿，俺老孙记性好着呢！你方才问俺是谁，俺说是齐天大圣孙悟空，然后又问俺会不会翻筋斗云……
```

第三问证明它记住了前两轮的内容。**这就是"记忆"的最小实现。**

> 💡 提示:`messages` 会无限增长,迟早超模型上下文窗口。怎么处理?—— 那是 **Stage 4 记忆** 要解决的问题。

---

## 2️⃣ 参数实验(`02_parameters.py`)

### 运行结果(真实观测)

| 实验 | 参数 | 结果 | finish_reason |
|------|------|------|---------------|
| A | temperature=0 | `春天把冬天藏起的琴弦挂满枝头…` | stop |
| A' | temperature=0 | `春天把冬天的沉默揉碎成千万颗嫩芽，` | **length** |
| B | temperature=1.5 | `撒成满山遍野的绿芽…` | stop |
| B' | temperature=1.5 | `把每片新叶都吹成会呼吸的翅膀` | stop |
| C | max_tokens=5 | (空内容) | **length** |
| D | seed=42 | `把藏了一冬的颜料打翻在枝头…` | stop |
| D' | seed=42 | `把冬天揉碎成雨…` | stop |

### 真实结论(和网上的理论不一样!)

1. **temperature=0 并不严格确定** —— A 和 A' 结果不同。说明 DeepSeek 服务端 temperature=0 时采样仍有随机性(有等价于 argmax 的保证仅部分模型提供)。
2. **temperature 越高越有"画面感"** —— 1.5 的结果明显更放飞。
3. **max_tokens=5 → 内容为空 + finish_reason=length** —— token 预算太小,模型还没输出第一个词就被掐断。**踩坑点**:max_tokens 别设太吝啬。
4. **seed 不能保证复现** —— D 和 D' 不同。DeepSeek 的 seed 只是"尽力而为"。

> 🕳️ 经验:`finish_reason` 字段是调参的仪表盘。看到 `length` 就说明输出被截断了;看到 `stop` 是正常结束。后面 Stage 2 还会见到第四种:`tool_calls`。

---

## 3️⃣ 流式输出(`03_streaming.py`)

### 原理

`stream=True` 时,`create()` 不再等全部结果,而是返回一个**迭代器**,模型每生成一小块就吐一次。

```python
stream = client.chat.completions.create(..., stream=True)
for chunk in stream:                          # 每个 chunk = 一小块输出
    piece = chunk.choices[0].delta.content    # 流式内容在 delta 里
    print(piece, end="", flush=True)          # flush=True 立即显示
```

### 运行结果(节选)

```
🤖 检索增强生成(RAG)是一种AI技术,先检索外部知识库中的相关文档,再输入给大语言模型,
从而生成更准确、最新的回答,减少幻觉。
```

> 💡 核心参数:`flush=True`,否则 Python 会把输出攒在缓冲区,看不到打字机效果。

---

## 4️⃣ 结构化输出(`04_structured_output.py`)

### 三段式套路(后面全程用到,背下来)

```
1. 定义结构  →  Pydantic 类(MovieReview)
2. 请求 JSON →  response_format={"type":"json_object"} + 提示词里说清字段
3. 校验数据  →  json.loads() + MovieReview.model_validate()
```

### 🕳️ 踩坑 1:把 JSON Schema 塞给模型,模型"原样抄作业"

**第一次失败**:我把 `MovieReview.model_json_schema()`(即 JSON Schema)直接写进 system,模型把它**当成要输出的内容原样返回**:

```json
{"properties": {"title": "流浪地球2", ...}, "required": [...], "title": "MovieReview", "type": "object"}
```

数据被嵌套进 `properties` 里,`model_validate()` 直接报 4 个字段缺失。

**修复**:不用 Schema 定义,改用**文字描述字段 + 一个输出示例**。示例长什么样,模型就照什么样输出。

```python
example = '{"title": "流浪地球2", "rating": 8.5, "pros": [...], "cons": [...], "summary": "..."}'
system = "只输出 JSON...\n字段要求:...\n输出示例:\n" + example
```

### 🕳️ 踩坑 2:`model_dump()` 不支持 `indent`

校验通过后打印格式化 JSON 报错 `unexpected keyword 'indent'`。`model_dump()` 返回的是 dict,格式化要用 `model_dump_json(indent=2)`。

### 最终运行结果

```json
{
  "title": "流浪地球2",
  "rating": 8.5,
  "pros": ["视觉特效震撼", "科幻设定硬核"],
  "cons": ["叙事节奏略有拖沓"],
  "summary": "中国科幻电影的新里程碑。"
}
```

评分:8.5 | 优点数:2 ✅ 校验通过

---

## ✍️ 动手练习

1. **01 多轮对话**:去掉 `messages.append({"role": "assistant", ...})` 那行,再跑第三问,对比"失忆"效果 —— 直观理解历史的重要性
2. **02 参数**:把 seed 改成不同值跑两次,感受效果;试试 `max_tokens=1` 看空输出
3. **03 流式**:删掉 `time.sleep(0.03)`,看真实生成速度;把回答改成长文
4. **04 结构化**:新定义一个 Pydantic 类(比如 `WeatherReport`:city / temperature / condition),让模型输出天气 JSON

## 📌 小结

> **这一阶段打通了 LLM 应用的四大基本功:上下文记忆、参数调优、流式体验、可靠的结构化输出。**
> 尤其是结构化输出 —— 下一阶段我们要让模型输出"调用工具的指令",用的正是这套"定义结构 → 请求 JSON → 校验"的方法。
