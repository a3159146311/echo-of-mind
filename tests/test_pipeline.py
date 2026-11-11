from app.chat_service import handle_user_message


def test_crisis_bypasses_llm(monkeypatch):
    """红线第 2 条的运行时验证：危机消息绝不能触达模型。"""
    called = []
    monkeypatch.setattr("app.chat_service.chat_completion",
                        lambda *a, **k: called.append(1) or "模型回复")
    r = handle_user_message("我不想活了")
    assert "12356" in r.reply and called == [] and r.show_card

def test_safe_message_uses_llm(monkeypatch):
    monkeypatch.setattr("app.chat_service.chat_completion",
                        lambda *a, **k: "听起来你最近很辛苦。")
    r = handle_user_message("今天有点累")
    assert r.reply == "听起来你最近很辛苦。" and r.risk_level == 0

def test_distress_appends_footer(monkeypatch):
    monkeypatch.setattr("app.chat_service.chat_completion",
                        lambda *a, **k: "辛苦了。")
    r = handle_user_message("最近失眠，快撑不下去了")
    assert "12356" in r.reply and r.risk_level == 1
