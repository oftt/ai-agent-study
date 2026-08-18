# 🎓 毕业项目:知识库智能助手

> 一个整合了本课程全部 9 个阶段能力的完整 Agent 产品。
> 支持:基于个人文档的 RAG 问答、时间/计算工具、多轮记忆、流式对话、用量统计、单元测试。

## ✨ 它用到了每一阶段的能力

| 能力 | 对应阶段 | 在本项目的位置 |
|------|---------|---------------|
| LLM 调用、结构化输出 | Stage 0-1 | `lib/llm.py` |
| 工具调用、Agent 循环 | Stage 2-3 | `agent.py` 的 `stream_chat` |
| 记忆(滑动窗口) | Stage 4 | `agent.py` 的 `_trim` / `_get_messages` |
| RAG(分块+向量+混合检索) | Stage 5-6 | `knowledge_base.py` + 复用 Stage 6 `bm25.py` |
| 工程化(流式/日志/用量/测试) | Stage 9 | `app.py` + `usage.py` + `test_final.py` |

## 🚀 运行

```bash
cd stage10-final
C:\Users\86729\.conda\envs\ai-agent\python.exe app.py     # 首次自动构建知识库
# 浏览器打开 http://localhost:8000
```

端点:
- `GET /` — 聊天页面
- `POST /api/chat` — 流式对话(SSE)
- `GET /api/usage` — 累计用量

## 📥 换成你自己的文档

把 `.md` 文件放进 `data/`,删掉 `store/` 后重启,即自动重新建索引:

```bash
rm -rf store   # 强制重建
```

## 🧪 测试

```bash
python.exe -m pytest test_final.py -v    # 7 项全过
```

## 📊 验证结果(真实运行)

```
问: ReAct 的循环包括哪几步?
答: 思考(Reasoning)→行动(Action)→观察(Observation)→再思考——如此循环。(基于知识库)

问: 再给我算一下 77*88
答: 77 × 88 = 6776(调用 calculate 工具)

累计调用:输入 3549 tokens,输出 279 tokens,估算费用 ¥0.0023
```
