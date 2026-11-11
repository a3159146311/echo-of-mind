from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app import diary
from app.chat_service import handle_user_message


@asynccontextmanager
async def lifespan(app: FastAPI):
    diary.init()   # 启动时：确保日记库就绪（含旧库自动迁移）
    yield          # ← 服务运行期间
    # 关闭时的清理逻辑写在这里；目前没有需要清理的资源


app = FastAPI(title="心语 EchoOfMind", version="0.3.0", lifespan=lifespan)


class ChatIn(BaseModel):
    message: str
    history: list[dict] = []


class ChatOut(BaseModel):
    reply: str
    risk_level: int
    show_card: bool
    hotlines: list | None


class UnlockIn(BaseModel):
    passphrase: str



@app.get("/api/health")
def health():
    return {"status": "ok", "unlocked": diary.is_unlocked()}


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.post("/api/chat", response_model=ChatOut)
def chat(body: ChatIn):
    r = handle_user_message(body.message, body.history or None)
    return ChatOut(reply=r.reply, risk_level=r.risk_level,
                   show_card=r.show_card, hotlines=r.hotlines)


@app.post("/api/unlock")
def unlock(body: UnlockIn):
    if not diary.unlock(body.passphrase):
        raise HTTPException(403, "口令不正确")
    return {"ok": True}


@app.post("/api/lock")
def lock():
    diary.lock()
    return {"ok": True}


@app.get("/api/diary")
def get_diary():
    try:
        return {"entries": diary.list_entries()}
    except PermissionError:
        raise HTTPException(423, "请先解锁日记")


@app.get("/api/trends")
def trends():
    """情绪趋势：仅解锁后可用。横轴是消息序号（v0.1 已知简化）。"""
    if not diary.is_unlocked():
        raise HTTPException(423, "请先解锁日记")
    entries = diary.list_entries(limit=100)
    points = [{"ts": e["ts"], "mood": e["mood"], "risk": e["risk"]}
              for e in reversed(entries) if e["mood"] is not None]
    emo: dict[str, int] = {}
    for e in entries:
        for k, v in (e.get("emotions") or {}).items():
            emo[k] = emo.get(k, 0) + v
    return {"points": points, "emotions": emo}
