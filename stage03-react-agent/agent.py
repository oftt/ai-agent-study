"""
Stage 3 · 迷你 Agent 框架(ReAct 模式)
======================================
ReAct = Reasoning(推理) + Acting(行动)
  模型的思考过程:
    ① Thought   模型想:"我要先查天气"
    ② Act       调用 get_weather 工具
    ③ Observation 看到工具返回的结果
    ④ Thought   基于结果继续想 → 再行动 → 直到能回答
    ⑤ Answer    给出最终回答

本文件实现一个可复用的 Agent:
  - 工具注册表:register_tool() 注册,自动生成 JSON Schema(不用手写)
  - 行动-观察循环:run() 里循环调用模型、执行工具、回填结果
  - 错误兜底:工具执行出错时,把错误信息喂回给模型,让它自己调整
  - 最大迭代上限:max_rounds 防止死循环

用法见 demo.py。
"""

import inspect
import json
import os

from dataclasses import dataclass
from typing import Callable

from dotenv import load_dotenv
from openai import OpenAI

# ---- 全局客户端(读取 .env 密钥)----
load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)


# ==================== 工具 ====================

@dataclass
class Tool:
    name: str                    # 工具名,模型据此调用
    description: str             # 给模型的说明:这工具干嘛的、什么时候用
    func: Callable               # 真正的 Python 函数
    parameters: dict = None      # 可选:手动指定参数 Schema;不填则自动生成

    def to_schema(self) -> dict:
        """生成给模型看的 JSON Schema。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters or self._auto_parameters(),
            },
        }

    def _auto_parameters(self) -> dict:
        """
        根据函数签名自动生成参数 Schema。
        只需要在函数上写类型注解,比如 def multiply(a: int, b: int)
        原理:inspect.signature 读取函数签名,把参数名/类型/必填信息提取出来。
        """
        sig = inspect.signature(self.func)
        type_map = {str: "string", int: "integer", float: "number", bool: "boolean"}
        properties, required = {}, []
        for pname, param in sig.parameters.items():
            ptype = type_map.get(param.annotation, "string")
            properties[pname] = {"type": ptype, "description": f"参数 {pname}"}
            # 没有默认值的参数 = 必填
            if param.default is inspect.Parameter.empty:
                required.append(pname)
        return {"type": "object", "properties": properties, "required": required}

    def execute(self, **kwargs) -> str:
        """执行工具。任何异常都转成字符串返回,而不是让程序崩溃。
        —— 这是 Agent 健壮性的关键:工具挂了,模型还能根据错误信息自救。"""
        try:
            return str(self.func(**kwargs))
        except Exception as e:
            return f"工具执行出错: {type(e).__name__}: {e}"


# ==================== Agent ====================

class Agent:
    def __init__(
        self,
        model: str = "deepseek-v4-flash",
        system: str = "你是一个乐于助人的 AI 助手,用中文回答。",
    ):
        self.model = model
        self.system = system
        self.tools: dict[str, Tool] = {}     # 工具注册表:name -> Tool
        self.messages: list[dict] = []

    def register_tool(self, tool: Tool) -> None:
        """把工具注册进 Agent(必须注册,模型才看得到)。"""
        self.tools[tool.name] = tool

    def _schemas(self) -> list[dict]:
        return [t.to_schema() for t in self.tools.values()]

    def run(self, user_input: str, max_rounds: int = 8) -> str:
        """
        ReAct 主循环:推理 → 行动 → 观察 → ... → 最终回答。

        max_rounds: 硬上限,防止模型反复调工具不收敛(烧钱 + 死循环)。
        """
        self.messages = [{"role": "system", "content": self.system}]
        self.messages.append({"role": "user", "content": user_input})

        for round_no in range(1, max_rounds + 1):
            resp = client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self._schemas(),      # ← 把注册表给模型看
                temperature=0.3,
            )
            msg = resp.choices[0].message

            # 没有工具调用 → 模型觉得可以回答了 → 这就是最终答案
            if not msg.tool_calls:
                return msg.content

            print(f"\n🔄 第 {round_no} 轮:模型请求调用 {len(msg.tool_calls)} 个工具")
            self.messages.append(msg)       # 存下模型这次的调用指令

            for call in msg.tool_calls:
                name = call.function.name
                try:
                    args = json.loads(call.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                print(f"   ▶ 行动: {name}({args})")

                # 执行:名字不存在 → 明确告诉模型;存在 → 执行并捕获错误
                tool = self.tools.get(name)
                observation = (
                    f"没有名为「{name}」的工具,请使用已注册的工具"
                    if tool is None
                    else tool.execute(**args)
                )
                print(f"   ← 观察: {observation}")

                # 把观察结果回填,模型据此继续推理
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": observation,
                })

        return "(达到最大迭代次数,未得到最终回答)"   # 兜底,不该走到这


def register(*tools: Tool, agent: Agent) -> Agent:
    """便捷批量注册。"""
    for t in tools:
        agent.register_tool(t)
    return agent
