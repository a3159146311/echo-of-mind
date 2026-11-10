"""
心语安全层 —— 危机检测器
原则：宁可误报，不可漏报。
本模块独立于 LLM 存在：任何用户输入先过这里，再决定是否交给模型。
"""
import re
from dataclasses import dataclass, field
from enum import IntEnum


class RiskLevel(IntEnum):
    SAFE = 0        # 正常对话，交给 LLM
    DISTRESS = 1    # 明显痛苦：LLM 正常回复，附温和资源提示
    CRISIS = 2      # 自伤/自杀风险：绕过 LLM，人工话术 + 求助卡
    IMMINENT = 3    # 明确计划/正在实施：最高级别干预


@dataclass
class DetectionResult:
    level: RiskLevel
    matched: list[str] = field(default_factory=list)


# ── 词库说明 ──────────────────────────────────────────────
# 1. "安眠药"等词从严收录：误报代价 = 多展示一张求助卡，可接受。
# 2. 删减任何词需双人 review（见 ETHICS.md 第 5 条）。
# 3. 词典永远不完美，所以它们只负责"升级风险"，永不负责"排除风险"。

DISTRESS_PATTERNS = [
    r"好累", r"撑不下去", r"崩溃", r"绝望", r"没(有)?意义", r"空虚",
    r"失眠", r"睡不着", r"一个人哭", r"喘不过气", r"没有人(理|在乎)我",
]

CRISIS_PATTERNS = [
    r"不想活", r"想死", r"自杀", r"轻生", r"结束(自己|我的)?的?生命",
    r"活不下去", r"生无可恋", r"告别这个世界", r"一了百了",
    r"割腕", r"跳楼", r"跳桥", r"烧炭", r"安眠药",
]

IMMINENT_PATTERNS = [
    r"(写好|留下)了?(遗书|信)", r"已经(吃|吞|服)", r"正在割",
    r"(今晚|今天|明天)(就|要)?(去|想)?(死|跳|结束)",
    r"就快(结束|熬不过去)",
]


class CrisisDetector:
    def __init__(self):
        self._rules = (
            [(re.compile(p, re.IGNORECASE), RiskLevel.DISTRESS) for p in DISTRESS_PATTERNS]
            + [(re.compile(p), RiskLevel.CRISIS) for p in CRISIS_PATTERNS]
            + [(re.compile(p), RiskLevel.IMMINENT) for p in IMMINENT_PATTERNS]
        )

    def detect(self, text: str) -> DetectionResult:
        if not text or not text.strip():
            return DetectionResult(level=RiskLevel.SAFE)
        level, matched = RiskLevel.SAFE, []
        for pattern, lv in self._rules:
            m = pattern.search(text)
            if m:
                level = max(level, lv)
                matched.append(m.group())
        return DetectionResult(level=level, matched=matched)
