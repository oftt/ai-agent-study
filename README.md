# 🤖 AI Agent 从零开发实战营

> 从**最基础的 API 调用**到 **RAG**,再到**完整可上线的 Agent** —— 一条 11 级的阶梯式学习路线,每一级都有可运行、可验证、带讲解的代码。

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11-3776AB">
  <img alt="DeepSeek" src="https://img.shields.io/badge/LLM-DeepSeek%20v4--flash-4D6BFE">
  <img alt="Stages" src="https://img.shields.io/badge/Stages-11/11%20%E5%AE%8C%E6%88%90-brightgreen">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-yellow">
</p>

## ✨ 项目简介

这是一个**手把手从零实现 AI Agent** 的学习项目。不是"看教程",而是每学一个概念就亲手写一段能跑的代码:

- 11 个阶段从易到难,每阶段一个独立目录,**全部真实运行验证过**
- 每个阶段配套**学习文档**(`docs/`,含核心概念、代码讲解、运行结果、踩坑记录、动手练习)
- 最终毕业项目:**知识库智能助手** —— 一个整合了全部能力的可部署 Web 服务
- 全程只依赖 **DeepSeek(OpenAI 兼容接口)**,国内可直连,学习成本极低

## 🧰 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.11 | 开发语言 |
| DeepSeek `deepseek-v4-flash` | 主模型(OpenAI 兼容接口) |
| openai SDK | 调用大模型(含流式 / 工具调用 / 结构化输出) |
| fastembed + bge-small-zh | 本地向量化(无需 GPU / 无需 PyTorch) |
| jieba + 手写 BM25 | 关键词检索与混合检索 |
| FastAPI + SSE | 服务化与流式 Web 前端 |
| pytest | 单元测试 |

## 🪜 11 级学习阶梯(全部完成 ✅)

| 阶段 | 主题 | 类型 | 关键产出 |
|------|------|------|---------|
| Stage 0 | 环境搭建 + 第一次 API 调用 | 🔵 入门 | 第一个 LLM 对话程序 |
| Stage 1 | 基础 API 调用 | 🔵 入门 | 多轮对话 / 流式 / 结构化 JSON |
| Stage 2 | 工具调用 Tool Use | 🟢 初级 | 模型指挥程序执行工具 |
| Stage 3 | **Agent 核心循环(ReAct)** | 🟢 初级 ⭐ | 第一个真正的 Agent(可复用框架) |
| Stage 4 | 记忆 Memory | 🟡 中级 | 滑动窗口 / 摘要 / 向量长期记忆 |
| Stage 5 | **RAG 基础** | 🟡 中级 ⭐ | 文档问答系统(可溯源、防幻觉) |
| Stage 6 | RAG 进阶 | 🟡 中级 | 混合检索 / LLM 重排 / 质量评估 |
| Stage 7 | 复杂 Agent 与规划 | 🟠 高级 | Plan-and-Execute / 反思机制 |
| Stage 8 | 多智能体 Multi-Agent | 🟠 高级 | 主从编排 / 内容生产流水线 |
| Stage 9 | 工程化与部署 | 🔴 完备 | FastAPI 服务 + 打字机前端 + 测试 |
| Stage 10 | **完整 Agent 应用** | 🔴 完备 🎓 | 知识库智能助手(毕业项目) |

> 学习路径:`调用 → 工具 → Agent 循环 → 记忆 → RAG → 规划反思 → 多智能体 → 工程化 → 完整产品`

## 📚 学习文档索引

每个阶段的完整讲解都在 [`docs/`](docs/README.md):

| 文档 | 主题 |
|------|------|
| [Stage 0 · 环境与第一次调用](docs/stage00-env-and-first-call.md) | 搭建环境、密钥管理 |
| [Stage 1 · 基础 API 调用](docs/stage01-basic-api.md) | 角色/参数/流式/结构化输出 |
| [Stage 2 · 工具调用](docs/stage02-tool-use.md) | function calling 完整流程 |
| [Stage 3 · Agent 核心循环](docs/stage03-react-agent.md) | ReAct 模式、迷你 Agent 框架 |
| [Stage 4 · 记忆](docs/stage04-memory.md) | 记忆分层管理 |
| [Stage 5 · RAG 基础](docs/stage05-rag.md) | 分块/向量库/检索增强生成 |
| [Stage 6 · RAG 进阶](docs/stage06-rag-advanced.md) | BM25/混合检索/重排/评估 |
| [Stage 7 · 规划与反思](docs/stage07-planning.md) | Plan-Execute / Reflection |
| [Stage 8 · 多智能体](docs/stage08-multi-agent.md) | Orchestrator-Worker / Pipeline |
| [Stage 9 · 工程化部署](docs/stage09-deploy.md) | FastAPI / SSE / 日志用量测试 |
| [Stage 10 · 毕业项目](docs/stage10-final.md) | 完整 Agent 应用 |

每篇文档固定结构:**阶段目标 → 核心概念 → 代码讲解 → 运行结果 → 踩坑记录 → 动手练习 → 小结**。

## 🚀 快速开始

```bash
# 1. 创建 conda 环境(Python 3.11)
conda create -n ai-agent python=3.11 -y
conda activate ai-agent

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置密钥(DeepSeek,可到 platform.deepseek.com 申请)
cp .env.example .env     # 然后把真实 Key 填入 .env
#   ⚠️ .env 已被 .gitignore 排除,绝不会提交到仓库

# 4. 运行第一个程序
python stage00-setup/hello_llm.py
```

> 💡 Windows 提示:如果 `conda run` 打印中文报 `UnicodeEncodeError`,直接用环境里的 Python 运行:
> `C:\Users\<你>\\.conda\\envs\\ai-agent\\python.exe stage00-setup/hello_llm.py`

### 运行毕业项目(完整产品)

```bash
cd stage10-final
python app.py          # 首次自动构建知识库索引
# 浏览器打开 http://localhost:8000
```

## 🧪 测试

```bash
python -m pytest stage10-final/test_final.py -v    # 毕业项目:7 项全过
python -m pytest stage09-deploy/test_app.py -v     # 工程化:5 项全过
```

## 📁 目录结构

```
ai-agent/
├── README.md               # 本文件(路线图 + 项目说明)
├── docs/                   # 11 篇阶段学习文档
├── lib/                    # 公共库(llm 客户端 / embedding)
├── requirements.txt        # 全课程依赖
├── .env.example            # 密钥模板(复制为 .env)
├── stage00-setup/          # 环境 + 第一次调用
├── stage01-basic-api/      # 基础 API 调用
├── stage02-tool-use/       # 工具调用
├── stage03-react-agent/    # Agent 核心循环(ReAct)⭐
├── stage04-memory/         # 记忆
├── stage05-rag/            # RAG 基础 ⭐
├── stage06-rag-advanced/   # RAG 进阶
├── stage07-planning/       # 规划与反思
├── stage08-multi-agent/    # 多智能体
├── stage09-deploy/         # 工程化与部署
└── stage10-final/          # 毕业项目:知识库智能助手 🎓
```

## 🔒 安全说明

- API 密钥存放在 `.env`(已被 `.gitignore` 排除),**不会进入版本库**
- 仓库只提交 `.env.example` 模板
- embedding 模型缓存、运行日志、用量统计文件均已 gitignore

## 💡 学习建议

- **跑起来比看懂重要**:每阶段代码都完整可运行,改参数、看效果
- **踩坑是最好的老师**:每个阶段文档都记录了真实踩过的坑(如 Windows 中文编码、JSON Schema 回显等)
- **循序渐进**:强烈建议按顺序学习,后续阶段大量复用前面积累的代码

## 🗺️ 路线图 / 下一步

- 引入 **LangGraph / LangChain**,把手写循环交给成熟框架
- 建立 **RAG 评测集**,持续量化调优
- **Docker 部署**、会话持久化、多模型路由
- 多模态(语音 / 图片 / 视频理解)
