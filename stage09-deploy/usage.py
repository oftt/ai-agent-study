"""
Stage 9 · 用量与成本统计
=========================
线上服务必须"算得清账":每次调用消耗多少 token、花了多少钱。
实现:累计计数 + 持久化到 JSON 文件 + 按单价估算费用。

价格说明:DeepSeek 官方价会变,这里用示例常量,可在 .env 或代码中调整。
"""

import json
from pathlib import Path

# 单价(元 / 百万 token)—— 示例值,请按官方最新价格调整
PRICE_INPUT = 0.5      # 输入
PRICE_OUTPUT = 2.0     # 输出


class UsageTracker:
    def __init__(self, log_file: str = "usage.json"):
        self.log_file = Path(log_file)
        self.total_prompt = 0
        self.total_completion = 0
        self._load()

    def add(self, prompt_tokens: int, completion_tokens: int) -> None:
        self.total_prompt += prompt_tokens
        self.total_completion += completion_tokens
        self._save()

    def cost(self) -> float:
        return (
            self.total_prompt / 1_000_000 * PRICE_INPUT
            + self.total_completion / 1_000_000 * PRICE_OUTPUT
        )

    def summary(self) -> str:
        return (
            f"累计调用:输入 {self.total_prompt} tokens,"
            f"输出 {self.total_completion} tokens,"
            f"估算费用 ¥{self.cost():.4f}"
        )

    def _save(self) -> None:
        self.log_file.write_text(json.dumps({
            "total_prompt": self.total_prompt,
            "total_completion": self.total_completion,
        }), encoding="utf-8")

    def _load(self) -> None:
        if self.log_file.exists():
            try:
                data = json.loads(self.log_file.read_text(encoding="utf-8"))
                self.total_prompt = data.get("total_prompt", 0)
                self.total_completion = data.get("total_completion", 0)
            except json.JSONDecodeError:
                pass
