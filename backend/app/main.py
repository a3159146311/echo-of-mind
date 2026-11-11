from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app import diary
from app.chat_service import handle_user_message

app = FastAPI(title="心语 EchoOfMind", version="0.2.0")


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


@app.on_event("startup")
def startup():
    diary.init()  # 首次启动生成口令文件 ~/.echoofmind/../backend/app/.diary_key


@app.get("/api/health")
def health():
    return {"status": "ok", "unlocked": diary.is_unlocked()}


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.post("/api/chat", response_model=ChatOut)
def chat(body: ChatIn):
    r = handle_user_message(body.message, body.history or None)
    diary.add_entry(body.message, r.reply, r.risk_level)  # 自动写入加密日记
    return ChatOut(reply=r.reply, risk_level=r.risk_level,
                   show_card=r.show_card, hotlines=r.hotlines)


@app.post("/api/unlock")
def unlock(body: UnlockIn):
    if not diary.unlock(body.passphrase):
        raise HTTPException(403, "口令不正确")
    return {"ok": True}


@app.get("/api/diary")
def get_diary():
    try:
        return {"entries": diary.list_entries()}
    except PermissionError:
        raise HTTPException(423, "请先解锁日记")

@app.post("/api/lock")
def lock():
    diary.lock()
    return {"ok": True}

