"""
Stage 3 · 演示:用迷你 Agent 完成多步任务
=========================================
演示两个能力:
  1. 多工具协作 —— 一个问题需要依次调用 计算器/时钟/知识库 三个工具
  2. 错误自救 —— 让工具抛异常(除以零),看模型如何根据错误信息调整回答

运行:
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe stage03-react-agent/demo.py
"""

from datetime import datetime

from agent import Agent, Tool


# ==================== 定义工具函数 ====================

def multiply(a: int, b: int) -> int:
    """乘法"""
    return a * b


def divide(a: float, b: float) -> float:
    """除法(故意不做保护,让除以零抛异常,测试 Agent 的容错)"""
    return a / b


def get_current_time() -> str:
    """当前时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S (%A)")


def get_weather(city: str) -> str:
    """模拟天气查询"""
    fake = {"北京": "晴,25°C", "上海": "多云,28°C", "广州": "雷阵雨,30°C"}
    return fake.get(city, f"{city}:暂无数据")


def search_knowledge(query: str) -> str:
    """迷你"知识库",模拟搜索/查资料"""
    kb = {
        "rag": "RAG(检索增强生成):先检索外部知识库中的相关文档,再交给大模型生成回答,"
               "能显著减少幻觉、回答最新信息。",
        "agent": "Agent:能感知环境、自主规划并调用工具来完成任务的人工智能系统。",
        "react": "ReAct:一种让模型交替进行 推理(Reasoning)与 行动(Acting)的 Agent 设计模式。",
    }
    q = query.lower()
    for key, value in kb.items():
        if key in q:
            return value
    return f"知识库中没有与「{query}」相关的信息。"


# ==================== 组装并运行 ====================

def build_agent() -> Agent:
    agent = Agent(
        system="你是一个计算与信息查询助手。需要算数就调计算器,"
               "需要时间就调时钟,需要知识就查知识库,最后用中文组织回答。"
    )
    for t in (
        Tool("multiply", "计算两个整数相乘", multiply),
        Tool("divide", "计算两个数相除", divide),
        Tool("get_current_time", "获取当前日期和时间", get_current_time),
        Tool("get_weather", "查询指定城市的天气,参数 city 为城市名", get_weather),
        Tool("search_knowledge", "在知识库中检索关键词并返回相关知识", search_knowledge),
    ):
        agent.register_tool(t)
    return agent


if __name__ == "__main__":
    agent = build_agent()

    print("#" * 60)
    print("# 任务 1:多工具协作(乘法 + 时间 + 查知识库)")
    print("#" * 60)
    answer1 = agent.run("帮我算一下 1234 × 5678 等于多少?今天几号星期几?顺便查一下 RAG 是什么。")
    print("\n🤖 最终回答:\n" + answer1)

    print("\n\n" + "#" * 60)
    print("# 任务 2:错误自救(除以零)")
    print("#" * 60)
    answer2 = agent.run("帮我算 5 ÷ 0 等于多少?")
    print("\n🤖 最终回答:\n" + answer2)
