"""
公共库 · 文本向量化(Embedding)
===============================
把一段文本变成一个"数字向量",语义相近的文本向量也相近。
这是记忆检索、RAG 检索的地基。

实现:fastembed(ONNX 运行时,无需 PyTorch)
  - 模型:BAAI/bge-small-zh-v1.5(中文效果好、体积小 ~100MB)
  - 国内网络:HF_ENDPOINT 指向 hf-mirror.com 镜像下载模型
  - 模型首次使用时自动下载到本地缓存,之后离线可用

用法:
  from lib.embed import embed, embed_many
  vec = embed("我喜欢喝美式咖啡")          # np.ndarray, shape=(512,)
  vecs = embed_many(["a", "b", "c"])
"""

import os
from functools import lru_cache
from pathlib import Path

# 国内下载模型走镜像(必须在 import fastembed 之前设置)
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
# 模型缓存到项目内 lib/.models,避免系统临时目录被清理后反复下载
os.environ.setdefault(
    "FASTEMBED_CACHE_PATH", str(Path(__file__).resolve().parent / ".models")
)

import numpy as np  # noqa: E402
from fastembed import TextEmbedding  # noqa: E402

MODEL_NAME = "BAAI/bge-small-zh-v1.5"


@lru_cache(maxsize=1)
def _get_model() -> TextEmbedding:
    """加载模型(只加载一次,缓存起来)。"""
    return TextEmbedding(MODEL_NAME)


def embed(text: str) -> np.ndarray:
    """单条文本 → 向量。"""
    return list(_get_model().embed([text]))[0]


def embed_many(texts: list[str]) -> list[np.ndarray]:
    """批量文本 → 向量列表。"""
    return list(_get_model().embed(texts))
