"""
Stage 4 · 短期记忆二:摘要压缩(Rolling Summary)
==============================================
比滑动窗口聪明:窗口满了,不直接丢掉老消息,
而是让模型把老消息"压缩成一段摘要"存起来。
之后每次对话都带上:摘要(远古记忆) + 最近几轮(近期记忆)。

优点:不丢失关键信息,且不占太多 token
缺点:每次压缩要调用一次模型(花小钱)

流程:
  历史攒够 N 条 → 调用模型概括成摘要 → 清空,只留摘要
  → 摘要随对话不断累加

运行:
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe stage04-memory/summary_memory.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # 以便 import lib

from lib.llm import MODEL, get_client  # noqa: E402

client = get_client()


class SummaryMemory:
    """摘要 + 近期消息 两段式记忆。"""

    def __init__(self, max_recent: int = 4, summary_max_tokens: int = 200):
        self.max_recent = max_recent     # 超过多少条就触发压缩
        self.summary_max_tokens = summary_max_tokens
        self.summary: str = ""           # 远古记忆(摘要)
        self.recent: list[dict] = []     # 近期完整消息

    def add(self, role: str, content: str) -> None:
        self.recent.append({"role": role, "content": content})
        if len(self.recent) >= self.max_recent:
            self._rollup()               # 攒够了 → 压缩

    def _rollup(self) -> None:
        """把近期消息压缩成一段摘要,合并进 summary,清空近期。"""
        transcript = "\n".join(
            f"{m['role']}: {m['content']}" for m in self.recent
        )
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": (
                    "你是对话摘要器。把下面这段对话压缩成一段简洁的中文摘要,"
                    "必须保留:用户个人信息、重要偏好、做出的承诺、尚未完成的事项。"
                )},
                {"role": "user", "content": transcript},
            ],
            temperature=0.2,
            max_tokens=self.summary_max_tokens,
        )
        new_summary = resp.choices[0].message.content.strip()
        self.summary = (self.summary + "\n" if self.summary else "") + new_summary
        self.recent = []
        print(f"\n  🗜️ [压缩触发] 近期消息 → 摘要已更新,当前摘要:\n  {self.summary}")

    def build_prompt(self) -> list[dict]:
        head = []
        if self.summary:
            head.append({
                "role": "system",
                "content": f"以下是更早对话的摘要(必要时引用):\n{self.summary}",
            })
        return [
            {"role": "system", "content": "你是一个乐于助人的助手,回答简洁。"},
            *head,
            *self.recent,
        ]

    def __len__(self):
        return len(self.recent)


if __name__ == "__main__":
    mem = SummaryMemory(max_recent=4)
    turns = [
        "我是程序员,正在学 AI Agent。",
        "我最喜欢的美式咖啡不加糖。",
        "今天工作好累。",
        "推荐一本轻松的书吧。",       # 攒满 4 条 → 触发压缩
        "我最近在学什么?",           # 信息在摘要里
        "我喝咖啡喜欢加什么?",       # 信息在摘要里
    ]
    for i, q in enumerate(turns, 1):
        mem.add("user", q)
        resp = client.chat.completions.create(
            model=MODEL, messages=mem.build_prompt(), temperature=0.3,
        )
        reply = resp.choices[0].message.content
        mem.add("assistant", reply)
        print(f"\n[第 {i} 轮] 用户: {q}")
        print(f"  助手: {reply}")
