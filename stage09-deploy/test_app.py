"""
Stage 9 · 单元测试
====================
线上服务必须有测试兜底。原则:
  - 只测"纯逻辑"(不调真实 LLM,不花真钱、不依赖网络)
  - 测试可复用、可缓存、可裁剪、可记账等工程能力

运行:
  cd stage09-deploy
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe -m pytest test_app.py -v
"""

import json

import pytest

from agent_service import ChatAgent, TTLCache
from usage import UsageTracker


# ---------- 工具缓存 ----------

def test_ttl_cache_hit_and_miss():
    c = TTLCache(ttl=60)
    c.set("a", 1)
    assert c.get("a") == 1                  # 未过期 → 命中
    c2 = TTLCache(ttl=-1)                   # 立刻过期
    c2.set("b", 2)
    assert c2.get("b") is None              # 过期 → 未命中


def test_weather_uses_cache():
    agent = ChatAgent(max_memory=20, usage=UsageTracker(log_file="_test_usage.json"))
    r1 = agent._execute("get_weather", json.dumps({"city": "北京"}))
    r2 = agent._execute("get_weather", json.dumps({"city": "北京"}))
    assert r1 == r2 == "晴,25°C"
    # 不同城市不共享缓存
    r3 = agent._execute("get_weather", json.dumps({"city": "上海"}))
    assert r3 == "多云,28°C"


# ---------- 记忆裁剪 ----------

def test_memory_trim_keeps_recent():
    agent = ChatAgent(max_memory=6)
    messages = [{"role": "system", "content": "s"}] + \
               [{"role": "user", "content": str(i)} for i in range(20)]
    agent._trim(messages)
    assert len(messages) == 7                # system + 最近 6 条
    assert messages[1]["content"] == "14"    # 最旧的被丢掉
    assert messages[-1]["content"] == "19"


# ---------- 工具错误兜底 ----------

def test_tool_error_captured():
    agent = ChatAgent(max_memory=6, usage=UsageTracker(log_file="_test_usage.json"))
    # calculate 收到非法字符 → 返回提示而非崩溃
    assert "非法" in agent._execute("calculate", json.dumps({"expr": "1; rm -rf /"}))
    # 未知工具 → 兜底消息
    assert "出错" in agent._execute("no_such_tool", "{}")


# ---------- 用量统计 ----------

def test_usage_cost():
    u = UsageTracker(log_file="_test_usage.json")
    u.add(1_000_000, 1_000_000)              # 各 100 万 token
    assert u.cost() == pytest.approx(0.5 + 2.0)   # 0.5 元输入 + 2.0 元输出
    assert "累计调用" in u.summary()
