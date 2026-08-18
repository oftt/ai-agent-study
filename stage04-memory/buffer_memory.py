"""
Stage 4 · 短期记忆一:滑动窗口
==============================
最简单粗暴的记忆策略:只保留最近 N 条消息,更早的直接丢掉。

优点:实现简单、不花钱(不调模型)
缺点:窗口之外的信息全部遗忘

关键概念:
  - 上下文窗口(Context Window):模型一次能"看到"的 token 上限
  - 现实约束:messages 无限增长会撑爆上下文窗口,所以必须裁剪
  - 设计细节:第一条 system 永远保留(模型的人设不能丢),其余按新老裁剪

运行:
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe stage04-memory/buffer_memory.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # 以便 import lib

from lib.llm import MODEL, get_client  # noqa: E402

client = get_client()

SYSTEM_PROMPT = "你是一个乐于助人的助手,回答简洁。"


class SlidingWindowMemory:
    """只保留最近 max_messages 条消息,第一条 system 永远保留。"""

    def __init__(self, max_messages: int = 6):
        self.max_messages = max_messages
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        # 超出窗口:丢最旧的,但永远保留第一条(system)
        if len(self.messages) > self.max_messages:
            excess = len(self.messages) - self.max_messages
            self.messages = self.messages[:1] + self.messages[1 + excess:]

    def build_prompt(self) -> list[dict]:
        """组装发送给模型的完整 messages。"""
        return self.messages

    def __len__(self):
        return len(self.messages)


def run_session(memory: SlidingWindowMemory, turns: list[str]) -> None:
    print(f"{'='*60}\n窗口上限 = {memory.max_messages} 条消息\n{'='*60}")
    for i, q in enumerate(turns, 1):
        memory.add("user", q)
        resp = client.chat.completions.create(
            model=MODEL, messages=memory.build_prompt(), temperature=0.3,
        )
        reply = resp.choices[0].message.content
        memory.add("assistant", reply)
        print(f"\n[第 {i} 轮] 用户: {q}")
        print(f"  窗口现有 {len(memory)} 条(含 system),模型只看到这些")
        print(f"  助手: {reply}")


if __name__ == "__main__":
    turns = [
        "我叫小明,住在上海。",                     # 第一句透露的"个人信息"
        "今天天气不错。",
        "推荐一家好吃的餐厅吧。",
        "你能记住我住在哪个城市吗?",                 # 考验:个人信息还在窗口里吗?
    ]
    # 窗口小的会遗忘,窗口大的记得 —— 对比运行效果
    print(">>>> 小窗口(max=2)<<<< 极小的窗口,只能装下最近一轮")
    small = SlidingWindowMemory(max_messages=2)
    run_session(small, turns)
    print("\n\n>>>> 大窗口(max=100)<<<<")
    big = SlidingWindowMemory(max_messages=100)
    run_session(big, turns)
