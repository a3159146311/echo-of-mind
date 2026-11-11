"""心语对话管线：任何用户消息的第一站永远是危机检测器。
CRISIS / IMMINENT 级别完全绕过 LLM——不拿用户的命赌概率。"""
from dataclasses import dataclass

from app import diary, referral
from app.llm_client import chat_completion
from app.safety.crisis_detector import CrisisDetector, RiskLevel
from app.safety.resources import get_intervention


@dataclass
class ChatResult:
    reply: str
    risk_level: int
    show_card: bool
    hotlines: list | None


def handle_user_message(text: str, history: list[dict] | None = None) -> ChatResult:
    detection = CrisisDetector().detect(text)
    intervention = get_intervention(detection.level)

    if detection.level in (RiskLevel.CRISIS, RiskLevel.IMMINENT):
        diary.add_entry(text, intervention["response"], int(detection.level))
        return ChatResult(
            reply=intervention["response"],
            risk_level=int(detection.level),
            show_card=True,
            hotlines=intervention["hotlines"],
        )

    reply = chat_completion(text, history)
    if intervention and intervention.get("footer"):
        reply = f"{reply}\n\n{intervention['footer']}"
    diary.add_entry(text, reply, int(detection.level))   # 日记存"模型原话"，转介属系统层不混入

    gentle = referral.maybe_referral()
    if gentle:
        reply = f"{reply}\n\n{gentle}"
    return ChatResult(reply=reply, risk_level=int(detection.level),
                      show_card=False, hotlines=None)
