# Stage 0 · 环境搭建与第一次 API 调用

> 日期:2026-08-18 · 状态:✅ 完成 · 源码:`stage00-setup/hello_llm.py`

## 🎯 阶段目标

- 建立可运行的 Python 开发环境(conda + 依赖)
- 学会管理 API 密钥(`.env`)
- 完成**第一次**与大模型的对话——打通过往 AI 应用的第一通电话

## 🧠 核心概念

### 1. 一次 LLM 调用 = 4 步

```
1. 创建客户端(携带密钥和服务器地址)
2. 构造对话 messages(说话的人 + 说的话)
3. 发送请求(指定模型和参数)
4. 取出回复
```

任何大模型应用(包括最终要做的 Agent)都是反复执行这 4 步。

### 2. messages 的三种角色

| 角色 | 作用 | 类比 |
|------|------|------|
| `system` | 给模型设定人设和规矩 | 入职培训手册 |
| `user` | 用户说的话 | 客户提问 |
| `assistant` | 模型之前的回答(多轮对话要用) | 上次的沟通记录 |

> ⚠️ **为什么 system 很重要**:大模型没有固定人设,你不告诉它"你是谁",它每次都可能自创风格。系统提示词是控制模型行为的**最便宜**的手段。

### 3. temperature:创造力旋钮

- 取值范围 **0 ~ 2**
- `0` → 每次回答几乎一样,适合确定性任务
- `0.7` → 默认值,日常对话
- `1.5`+ → 天马行空,适合写诗/脑暴

原理:模型每次从候选词里按概率抽样,temperature 控制这个概率分布的"尖锐程度"。

### 4. Token:计费单位

- 模型读写的最小单位,中文大约 1 字 ≈ 1~2 token,英文约 1 词 ≈ 1.3 token
- 输入 + 输出都计费,输入便宜、输出贵
- 本次调用消耗:**输入 105 + 输出 125 = 230 token**

## 💻 代码讲解(hello_llm.py)

```python
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()   # 读取项目根目录 .env 里的密钥
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",   # DeepSeek 与 OpenAI 接口兼容
)

messages = [
    {"role": "system", "content": "你是一位严谨的中文技术讲师..."},
    {"role": "user", "content": "请用一句话告诉我:什么是 AI Agent?"},
]

response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=messages,
    temperature=0.7,
)
reply = response.choices[0].message.content
```

### 运行结果

```
模型回复: AI Agent 是一种能够感知环境、自主规划决策并调用工具执行任务,以达成特定目标的智能系统。
本次用量: 输入 tokens = 105 | 输出 tokens = 125
```

## 🕳️ 踩坑记录(重要!)

这一阶段踩了 3 个坑,都是 Windows + 国内网络环境的经典问题:

### 坑 1:conda 源失效(TUNA 镜像 404)
- **现象**:`conda create` 报 `HTTP 404 NOT FOUND for channel anaconda/pkgs/r`
- **原因**:`.condarc` 里配置的清华 TUNA 镜像 `pkgs/*` 频道已失效
- **解决**:`--override-channels` 绕过 `.condarc`,改用官方源;官方源需要先 `conda tos accept` 接受服务条款

### 坑 2:conda run 打印中文崩溃
- **现象**:`conda run -n ai-agent python xxx.py` 报 `UnicodeEncodeError: 'gbk' codec can't encode`
- **原因**:Windows 中文系统控制台默认 GBK 编码,conda run 捕获输出后转码失败
- **解决**:不经过 conda run,直接用环境内 python 运行,并设 `PYTHONUTF8=1`:
  ```
  C:\Users\86729\.conda\envs\ai-agent\python.exe stage00-setup/hello_llm.py
  ```
- **经验**:以后本项目所有脚本都用这个方式运行

### 坑 3:Git Bash 传中文 JSON 编码错误
- **现象**:curl 直接发中文请求体报 `invalid unicode code point`
- **解决**:用 Python SDK 发请求(它正确处理 UTF-8),别用 shell 拼 JSON

## ✍️ 动手练习

打开 `stage00-setup/hello_llm.py` 各改一处、各跑一次:

1. **改人设**:system 改成 `"你是一个毒舌吐槽的科技博主"`,看语气变化
2. **改温度**:`temperature` 分别设 `0` 和 `1.5`,对比两次回答的差异
3. **改问题**:user 换成你自己真正想问的问题

## 📌 小结

> **LLM 调用 = 客户端 + messages + 参数,四步走完,通电话打通了。**
> 你已经具备了构建 AI Agent 的最小基础——接下来所有功能(工具、记忆、RAG)都建立在这 4 步之上。
