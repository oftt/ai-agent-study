"""
毕业项目 · 服务入口
====================
知识库智能助手服务(整合 RAG + 工具 + 记忆 + 流式 + 用量)。

启动(首次会自动构建知识库索引):
  cd stage10-final
  C:\\Users\\86729\\.conda\\envs\\ai-agent\\python.exe app.py
  浏览器打开 http://localhost:8000
"""

import json
import logging
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import FinalAgent  # noqa: E402
from knowledge_base import KnowledgeBase, STORE_DIR  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.FileHandler("final_agent.log", encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger("final")

app = FastAPI(title="知识库智能助手")

# 加载(或构建)知识库 + 创建 Agent —— 服务启动时完成
if (STORE_DIR / "vectors.npy").exists():
    kb = KnowledgeBase.load()
    logger.info("加载已有知识库:%d 片段", len(kb))
else:
    logger.info("构建知识库...")
    kb = KnowledgeBase().build()
agent = FinalAgent(kb)


class ChatIn(BaseModel):
    session_id: str
    message: str


@app.get("/", response_class=HTMLResponse)
def index():
    return (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")


@app.post("/api/chat")
def chat(req: ChatIn):
    def gen():
        try:
            for ev in agent.stream_chat(req.session_id, req.message):
                yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.exception("处理异常")
            yield f"data: {json.dumps({'delta': '服务开小差了: ' + str(e)}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/usage")
def usage():
    return {"summary": agent.usage.summary()}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
