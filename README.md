# 🤖 AI Agent 从零开发 · 学习路线图

> 从最基础的 API 调用,到 RAG,再到完整可用的 Agent。
> 技术栈:**DeepSeek (OpenAI 兼容接口) + Python 3.11**

## 🪜 阶梯总览(由浅入深)

| 阶段 | 主题 | 类型 | 状态 |
|------|------|------|------|
| Stage 0 | 环境搭建 + 第一次 API 调用 | 🔵 入门 | ✅ 完成 |
| Stage 1 | 基础 API 调用(角色/参数/流式/结构化输出) | 🔵 入门 | ✅ 完成 |
| Stage 2 | 工具调用 Tool Use(function calling) | 🟢 初级 | ✅ 完成 |
| Stage 3 | Agent 核心循环(ReAct)**里程碑** | 🟢 初级 | ✅ 完成 |
| Stage 4 | 记忆 Memory | 🟡 中级 | ⏳ 待开始 |
| Stage 5 | RAG 基础 **里程碑** | 🟡 中级 | ⏳ 待开始 |
| Stage 6 | RAG 进阶(混合检索/重排/评估) | 🟡 中级 | ⏳ 待开始 |
| Stage 7 | 复杂 Agent 与规划(Plan-and-Execute) | 🟠 高级 | ⏳ 待开始 |
| Stage 8 | 多智能体 Multi-Agent | 🟠 高级 | ⏳ 待开始 |
| Stage 9 | 工程化与部署(FastAPI + Web 前端) | 🔴 完备 | ⏳ 待开始 |
| Stage 10 | 完整 Agent 应用(毕业项目) | 🔴 完备 | ⏳ 待开始 |

## 📁 目录结构

```
ai-agent/
├── README.md               # 本路线图
├── .env.example            # 密钥模板(复制为 .env 填真实密钥)
├── requirements.txt        # Python 依赖
├── stage00-setup/          # 环境 + 第一次调用
├── stage01-basic-api/      # 基础 API 调用
├── stage02-tool-use/       # 工具调用
├── stage03-react-agent/    # Agent 核心循环
├── ...(后续阶段逐级建立)
```

## 🚀 快速开始

```bash
# 1. 创建并激活 conda 环境
conda create -n ai-agent python=3.11 -y
conda activate ai-agent

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置密钥
#    复制 .env.example 为 .env,填入你的 DeepSeek API Key
#    申请地址:https://platform.deepseek.com/api_keys

# 4. 运行第一个程序
#   (Windows 上 conda run 打印中文会崩溃,直接用环境 python 运行)
C:\Users\86729\.conda\envs\ai-agent\python.exe stage00-setup/hello_llm.py
```

## 📚 学习小贴士

- 每一阶段代码都**完整可运行**,跑起来、改参数、看效果,比只读代码重要得多
- 每阶结束会有一个"动手练习",想加深就做,跳过也不影响继续
- 遇到问题先用 `print()` 和报错信息定位,再看注释
