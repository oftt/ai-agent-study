"""
公共库 · LLM 客户端
====================
所有阶段共用一个 OpenAI 兼容客户端(DeepSeek)。
抽成公共模块:客户端只需创建一次,各脚本复用。

设置项:
  DEEPSEEK_API_KEY  密钥(来自 .env)
  LLM_MODEL         模型名,默认 deepseek-v4-flash
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()          # 从项目根 .env 读取密钥

MODEL = os.getenv("LLM_MODEL", "deepseek-v4-flash")

_client = None


def get_client() -> OpenAI:
    """懒加载:只有第一次调用才真正创建客户端。"""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
        )
    return _client
