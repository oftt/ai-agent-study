# Stage 9 · 工程化与部署

> 日期:2026-08-18 · 状态:✅ 完成 · 源码:`stage09-deploy/`(`app.py` + `agent_service.py` + `usage.py` + `test_app.py` + `static/index.html`)

## 🎯 阶段目标

- 把 Agent 包成**可上线的 Web 服务**(FastAPI)
- **流式 SSE** 给前端打字机效果
- 工程四件套:**日志 / 用量统计 / 工具缓存 / 单元测试**
- 架构分层:业务逻辑(agent_service)与 Web 传输(app)解耦

---

## 🏗️ 架构分层

```
app.py             FastAPI 层:路由、SSE 流、异常兜底      ← 只管"传输"
agent_service.py   Agent 核心:记忆/工具/流式/用量/缓存    ← 只管"业务"
usage.py           用量与费用统计(JSON 持久化)
static/index.html  聊天前端(读取 SSE,打字机效果)
test_app.py        单元测试(只测纯逻辑,不调真 LLM)
```

> 💡 **为什么分层**:Web 层天天改(加路由、换鉴权),业务层稳定(Agent 逻辑)。分层后改 Web 不动业务,还能单独测业务。

---

## 🔑 关键技术点

### 1. 流式 SSE(Server-Sent Events)

服务端:
```python
@app.post("/api/chat")
def chat(req):
    def gen():
        for ev in agent.stream_chat(...):        # 业务层是生成器
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"   # SSE 格式
        yield "data: [DONE]\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")
```

前端:用 `fetch` 的 `ReadableStream` 逐块读,按 `\n\n` 切事件,`textContent += delta` 实现打字机。

### 2. 流式 + 工具调用共存

```python
stream_options={"include_usage": True}   # 流式也能拿到用量
# 工具调用的 delta 里没有 content → 前端不会看到"杂音"
# tool_calls 是分段拼出来的:name/arguments 要逐块拼接
```

验证结果:模型内部静默调用了 `get_current_time` + `calculate` 两个工具,然后流式输出最终回答,前端只看到干净的文本。

### 3. 工程四件套

| 能力 | 实现 | 验证 |
|------|------|------|
| **日志** | logging → 控制台 + `agent.log` 文件 | 日志完整记录"收到消息→请求工具→执行→回答" |
| **用量** | `UsageTracker`:累计 token + 按单价估费,JSON 持久化 | 一次调用:输入1030/输出61,¥0.0006 |
| **缓存** | `TTLCache`:天气同城 5 分钟不重查 | 测试验证命中/过期 |
| **测试** | pytest,只测纯逻辑(不调真 LLM) | **5/5 通过** |

### 4. 安全细节

- `calculate` 用**白名单**校验表达式字符,再用空 `__builtins__` 的 eval —— 防止模型诱导执行恶意代码
- 服务端 `try/except` 兜底,异常也返回 SSE 而不是裸奔 500

---

## 🚀 运行方式

```bash
cd stage09-deploy
C:\Users\86729\.conda\envs\ai-agent\python.exe app.py
# 浏览器打开 http://localhost:8000
```

端点:
- `GET /` —— 聊天页面(打字机效果)
- `POST /api/chat` —— 流式对话(session_id + message)
- `GET /api/usage` —— 累计用量

---

## 🕳️ 踩坑记录

| 坑 | 现象 | 解法 |
|----|------|------|
| Git Bash curl 传中文 | 400 "error parsing the body" | shell 传 UTF-8 中文会乱码,测试用 ASCII 或直接用浏览器 |
| 流式拿不到用量 | `stream.usage` 为 None | 加 `stream_options={"include_usage": True}` |
| usage/日志文件混进 git | 运行时产物污染仓库 | `.gitignore` 加 `usage.json`、`*.log`、`.pytest_cache/` |

## ✍️ 动手练习

1. 浏览器打开 `http://localhost:8000`,连续聊几句(测试记忆),再问"我们刚才聊了什么"
2. 给 `/api/chat` 加一个"消息长度上限"校验(比如超过 500 字返回 400),体验服务端参数校验
3. 把 `TTLCache` 的 ttl 改成 5 秒,连问两次"北京天气",对比日志里缓存命中与否
4. 在 `test_app.py` 里给 `_trim` 写一个"会话过多"的边界测试(比如 0 条消息)

## 📌 小结

> **从"能跑的脚本"到"能上线的服务" = 分层架构 + 流式传输 + 日志/用量/缓存/测试。**
> 你的 Agent 已经具备产品形态了。最后一阶:把它做成一个**完整、有真实场景的毕业项目**。
