"""
Stage 9 · FastAPI 服务层
=========================
把 Agent 包成 Web 服务:
  GET  /api/usage  查看累计用量
  POST /api/chat   流式对话(SSE 协议)
  GET  /           聊天前端页面

启动:
  cd stage09-deploy
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe app.py
  然后浏览器打开 http://localhost:8000
"""

import json
import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from agent_service import ChatAgent

# ---- 日志:控制台 + 文件(线上服务必须留痕)----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("agent.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("app")

app = FastAPI(title="我的 AI Agent 服务")
agent = ChatAgent()


class ChatIn(BaseModel):
    session_id: str
    message: str


@app.get("/", response_class=HTMLResponse)
def index():
    return (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")


@app.post("/api/chat")
def chat(req: ChatIn):
    logger.info("收到消息 session=%s len=%d", req.session_id, len(req.message))

    def gen():
        try:
            for ev in agent.stream_chat(req.session_id, req.message):
                # SSE 格式:每行 data: 开头,空行结束一个事件
                yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
        except Exception as e:                        # 服务端绝不能裸奔
            logger.exception("处理消息异常")
            yield f"data: {json.dumps({'delta': '服务开小差了: ' + str(e)}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/usage")
def usage():
    return {"summary": agent.usage.summary()}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
