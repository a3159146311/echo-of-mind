"""温和转介：持续的沉重信号不应被无视，也不应吓到人。
三原则：低频（24h 冷却）、轻声（措辞不带 alarm）、留白（只提示，不追问）。"""
import time

from app import diary

REFERRAL_TEXT = (
    "想轻轻跟你说一句：最近几天的对话里，沉重的感觉出现了好几次。"
    "我会一直在，陪你慢慢聊。也想让你知道：如果这种状态已经持续了很久，"
    "和一位专业的心理咨询师聊聊，也是一种对自己的照顾——"
    "这不是软弱，就像感冒了去看医生一样自然。\n"
    "☎ 全国心理援助热线：12356（24小时，免费）"
)
WINDOW = 5        # 看最近 5 条
MIN_DATA = 3      # 至少 3 条有评分的数据才判断
THRESHOLD = 3     # 其中 ≥3 条沉重才转介
COOLDOWN = 24 * 3600


def _is_heavy(e: dict) -> bool:
    return e["risk"] >= 1 or (e["mood"] is not None and e["mood"] <= 1)


def maybe_referral() -> str | None:
    if not diary.is_unlocked():
        return None
    recent = [e for e in diary.list_entries(limit=WINDOW) if e["mood"] is not None]
    if len(recent) < MIN_DATA:
        return None
    if sum(_is_heavy(e) for e in recent) < THRESHOLD:
        return None
    now = int(time.time())
    if now - diary.get_meta_int("last_referral") < COOLDOWN:
        return None
    diary.set_meta_int("last_referral", now)   # 记录触发时刻 = 启动冷却
    return REFERRAL_TEXT
