from fastapi import FastAPI
from pydantic import BaseModel

from app.chat_service import handle_user_message

app = FastAPI(title="心语 EchoOfMind", version="0.1.0")


class ChatIn(BaseModel):
    message: str
    history: list[dict] = []


class ChatOut(BaseModel):
    reply: str
    risk_level: int
    show_card: bool
    hotlines: list | None


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "echo-of-mind"}


@app.post("/api/chat", response_model=ChatOut)
def chat(body: ChatIn):
    result = handle_user_message(body.message, body.history or None)
    return ChatOut(reply=result.reply, risk_level=result.risk_level,
                   show_card=result.show_card, hotlines=result.hotlines)
