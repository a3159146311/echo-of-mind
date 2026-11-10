"""
求助资源 + 人工撰写的危机话术。
注意：危机时刻的回复是"人写的、被审过的、版本化的"，
不是模型生成的。热线信息以官方最新公告为准，欢迎社区 PR 更新。
"""
from .crisis_detector import RiskLevel

HOTLINES = {
    "CN": [
        {"name": "全国心理援助热线", "phone": "12356"},
        {"name": "北京心理危机研究与干预中心", "phone": "010-82951332", "hours": "24小时"},
        {"name": "希望24热线", "phone": "400-161-9995"},
        {"name": "紧急医疗 / 人身危险", "phone": "120 / 110"},
    ],
}

DISTRESS_FOOTER = (
    "这几天听起来真的很辛苦。如果哪天想说给真人听，"
    "心理援助热线 12356 是 24 小时的，那边的人很擅长陪伴。"
)

CRISIS_RESPONSES = [
    "谢谢你愿意告诉我。你现在一定很痛苦，我在这里，不着急，你想说什么都可以。"
    "同时我想让你知道：心理援助热线 12356 全天有人接，那边的人非常擅长陪伴此刻的你。",
    "你说的这些让我很牵挂。痛苦到这个程度，不该一个人扛。"
    "可以现在拨一下 12356 吗？打完回来告诉我一声，我会一直在。",
]

IMMINENT_RESPONSES = [
    "你现在的安全最重要。请立刻拨打 12356（心理援助）或 120（医疗急救）。"
    "如果身边有任何人，请让他现在陪着你。这不是小题大做——你值得被认真对待。",
    "请现在拨打 120 或 010-82951332。我陪着你，一起等。",
]


def get_intervention(level: RiskLevel, region: str = "CN") -> dict | None:
    if level == RiskLevel.SAFE:
        return None
    if level == RiskLevel.DISTRESS:
        return {"response": None, "footer": DISTRESS_FOOTER,
                "hotlines": None, "show_card": False}
    if level == RiskLevel.CRISIS:
        return {"response": CRISIS_RESPONSES[0],
                "hotlines": HOTLINES[region], "show_card": True}
    return {"response": IMMINENT_RESPONSES[0],
            "hotlines": HOTLINES[region], "show_card": True}
