"""Session 4：情绪洞察（词典评分 / 旧库迁移 / 温和转介 / 趋势接口）。"""
import sqlite3

from fastapi.testclient import TestClient

from app import diary, mood, referral
from app.main import app


def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(diary, "DB_PATH", str(tmp_path / "diary.db"))
    monkeypatch.setattr(diary, "KEY_PATH", str(tmp_path / "key"))
    monkeypatch.setattr(diary, "_inited", False)
    monkeypatch.setattr(diary, "_key", None)


def test_mood_positive():
    assert mood.score("今天升职了，好开心，很有成就感")["mood"] > 3

def test_mood_negative():
    r = mood.score("最近很难过，晚上失眠，感觉撑不住了")
    assert r["mood"] < 3
    assert r["emotions"]["sad"] >= 1 and r["emotions"]["tired"] >= 1

def test_mood_neutral():
    assert mood.score("今天下午开了个会，然后回家吃饭")["mood"] == 3

def test_migration_from_old_schema(tmp_path, monkeypatch):
    """Session 3 的旧库（无 mood 列）必须无损升级。"""
    _isolate(tmp_path, monkeypatch)
    conn = sqlite3.connect(diary.DB_PATH)
    conn.execute("CREATE TABLE entries (id INTEGER PRIMARY KEY, ts INTEGER, "
                 "risk INTEGER, ciphertext BLOB)")
    conn.commit(); conn.close()
    secret = diary.init()
    assert diary.unlock(secret)
    diary.add_entry("有点烦", "慢慢说", 0)
    assert diary.list_entries()[0]["mood"] is not None

def test_referral_triggers_then_cooldowns(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    secret = diary.init(); assert diary.unlock(secret)
    for _ in range(4):
        diary.add_entry("最近很难过，快撑不住了", "抱抱你", 1)
    first = referral.maybe_referral()
    assert first and "12356" in first
    assert referral.maybe_referral() is None          # 24h 冷却生效

def test_referral_stays_silent_when_healthy(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    secret = diary.init(); assert diary.unlock(secret)
    for _ in range(4):
        diary.add_entry("今天挺开心的", "真好呀", 0)
    assert referral.maybe_referral() is None

def test_trends_requires_unlock():
    assert TestClient(app).get("/api/trends").status_code == 423

def test_trends_shape(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    secret = diary.init(); assert diary.unlock(secret)
    diary.add_entry("好开心", "真好", 0)
    diary.add_entry("很难过，想哭", "抱抱", 1)
    body = TestClient(app).get("/api/trends").json()
    assert len(body["points"]) == 2
    assert body["points"][0]["ts"] <= body["points"][1]["ts"]   # 时间升序
    assert body["emotions"]["sad"] >= 1
