import os
import pytest
from app import diary


@pytest.fixture
def d(tmp_path, monkeypatch):
    """隔离环境：假数据库路径 + 重置模块内部状态，绝不碰用户真实日记。"""
    monkeypatch.setattr(diary, "DB_PATH", str(tmp_path / "diary.db"))
    monkeypatch.setattr(diary, "KEY_PATH", str(tmp_path / "key"))
    monkeypatch.setattr(diary, "_inited", False)
    monkeypatch.setattr(diary, "_key", None)
    return diary


def test_init_creates_key_file(d):
    secret = d.init()
    assert secret and os.path.exists(d.KEY_PATH)


def test_init_is_idempotent(d):
    """重复调用 init 不会重新生成口令。"""
    first = d.init()
    second = d.init()
    assert first and second == ""


def test_unlock_roundtrip(d):
    secret = d.init()
    assert d.unlock("错误口令") is False
    assert d.unlock(secret) is True


def test_entries_encrypted_at_rest(d):
    secret = d.init()
    d.unlock(secret)
    d.add_entry("今天心情不好", "辛苦了。", risk=0)
    raw = open(d.DB_PATH, "rb").read()
    assert "心情不好".encode("utf-8") not in raw
    assert "辛苦".encode("utf-8") not in raw


def test_list_entries_requires_unlock(d):
    d.init()
    with pytest.raises(PermissionError):
        d.list_entries()

def test_lock_clears_access(d):
    secret = d.init()
    d.unlock(secret)
    d.add_entry("测试", "回复", 0)
    d.lock()
    assert d.is_unlocked() is False
    with pytest.raises(PermissionError):
        d.list_entries()

