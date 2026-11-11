"""基于词典的轻量情绪评分（离线、确定、零成本）。
局限：不理解反讽与语境。单条评分只用于画曲线，从不单独触发任何动作。"""

EMOTION_LEXICON = {
    "sad":     ["难过", "伤心", "沮丧", "失落", "想哭", "哭", "抑郁", "郁闷",
                "心痛", "委屈", "绝望", "消沉", "低落"],
    "anxious": ["焦虑", "紧张", "担心", "害怕", "恐惧", "慌", "压力", "不安",
                "崩溃", "发愁"],
    "angry":   ["生气", "愤怒", "火大", "气死", "讨厌", "恨", "烦躁", "烦"],
    "tired":   ["累", "疲惫", "倦", "失眠", "睡不着", "撑不住", "麻木", "耗尽",
                "提不起"],
    "lonely":  ["孤独", "寂寞", "没人在乎", "空虚", "被忽视"],
    "positive": ["开心", "高兴", "快乐", "幸福", "轻松", "满意", "兴奋", "期待",
                 "感恩", "平静", "安心", "舒服", "放松", "不错"],
}
WEIGHTS = {"sad": 1.0, "anxious": 1.0, "angry": 1.0,
           "lonely": 1.0, "tired": 0.5, "positive": 1.0}
BASE = 3  # mood ∈ [0, 6]：0 沉重 → 3 中性 → 6 明亮


def score(text: str) -> dict:
    emotions = {name: sum(text.count(kw) for kw in kws)
                for name, kws in EMOTION_LEXICON.items()}
    delta = (WEIGHTS["positive"] * emotions["positive"]
             - sum(w * emotions[n] for n, w in WEIGHTS.items() if n != "positive"))
    mood = max(0, min(6, round(BASE + delta)))
    return {"mood": mood, "emotions": emotions}
