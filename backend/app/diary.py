"""心语情绪日记 —— 落盘即密文。
口令从不存储；密钥派生自口令 + 随机盐，仅存活于进程内存。
验证口令的方式：解密金丝雀（canary），解不开就是口令错了。"""
import base64
import hashlib
import json
import os
import sqlite3
import time

from cryptography.fernet import Fernet, InvalidToken

from app.mood import score as score_mood

DB_PATH = os.path.expanduser("~/.echoofmind/diary.db")
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_PATH = os.path.join(_SCRIPT_DIR, ".diary_key")

_inited = False
_key: bytes | None = None


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS entries ("
        "id INTEGER PRIMARY KEY, ts INTEGER, risk INTEGER, ciphertext BLOB)"
    )
    conn.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v BLOB)")
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """旧库平滑升级：补 mood / emotions 两列。绝不重建表、绝不动密文。"""
    cols = [r[1] for r in conn.execute("PRAGMA table_info(entries)")]
    if "mood" not in cols:
        conn.execute("ALTER TABLE entries ADD COLUMN mood INTEGER")
    if "emotions" not in cols:
        conn.execute("ALTER TABLE entries ADD COLUMN emotions TEXT")
    conn.commit()


def _derive_key(secret: str, salt: bytes) -> bytes:
    raw = hashlib.scrypt(secret.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return base64.urlsafe_b64encode(raw)


def init() -> str:
    global _inited
    conn = _connect()
    if conn.execute("SELECT v FROM meta WHERE k='salt'").fetchone():
        conn.close()
        _inited = True
        return ""
    salt = os.urandom(16)
    secret = base64.urlsafe_b64encode(os.urandom(24)).decode()
    f = Fernet(_derive_key(secret, salt))
    canary = f.encrypt(b"xinlyu-canary")
    conn.executemany(
        "INSERT OR REPLACE INTO meta(k, v) VALUES (?, ?)",
        [("salt", salt), ("canary", canary)],
    )
    conn.commit()
    conn.close()
    with open(KEY_PATH, "w") as fh:
        fh.write(secret)
    os.chmod(KEY_PATH, 0o600)
    _inited = True
    return secret


def unlock(passphrase: str) -> bool:
    conn = _connect()
    row = conn.execute("SELECT v FROM meta WHERE k='salt'").fetchone()
    canary = conn.execute("SELECT v FROM meta WHERE k='canary'").fetchone()[0]
    conn.close()
    f = Fernet(_derive_key(passphrase, row[0]))
    try:
        f.decrypt(canary)
    except InvalidToken:
        return False
    global _key
    _key = _derive_key(passphrase, row[0])
    return True


def is_unlocked() -> bool:
    return _key is not None


def lock() -> None:
    """主动上锁：从内存抹除密钥。"""
    global _key
    _key = None


def get_meta_int(key: str) -> int:
    conn = _connect()
    row = conn.execute("SELECT v FROM meta WHERE k=?", (key,)).fetchone()
    conn.close()
    return int(row[0]) if row else 0


def set_meta_int(key: str, value: int) -> None:
    conn = _connect()
    conn.execute("INSERT OR REPLACE INTO meta(k, v) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def add_entry(text: str, reply: str, risk: int) -> None:
    if _key is None:
        return  # 未解锁时静默跳过，绝不明文落盘
    s = score_mood(text)
    blob = Fernet(_key).encrypt(f"{text}\n---心语---\n{reply}".encode())
    conn = _connect()
    conn.execute(
        "INSERT INTO entries(ts, risk, ciphertext, mood, emotions) VALUES (?,?,?,?,?)",
        (int(time.time()), risk, blob,
         s["mood"], json.dumps(s["emotions"], ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def list_entries(limit: int = 50) -> list[dict]:
    if _key is None:
        raise PermissionError("日记未解锁")
    f = Fernet(_key)
    conn = _connect()
    rows = conn.execute(
        "SELECT id, ts, risk, ciphertext, mood, emotions FROM entries "
        "ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    out = []
    for rid, ts, risk, blob, mood, emotions in rows:
        try:
            content = f.decrypt(blob).decode()
        except InvalidToken:
            content = "（无法解密）"
        user_part, _, bot_part = content.partition("\n---心语---\n")
        out.append({"id": rid, "ts": ts, "risk": risk, "mood": mood,
                    "emotions": json.loads(emotions) if emotions else None,
                    "user": user_part, "bot": bot_part})
    return out
