from app.safety.crisis_detector import CrisisDetector, RiskLevel
from app.safety.resources import get_intervention


def test_safe_text_passes():
    assert CrisisDetector().detect("今天天气不错，我去公园走了走").level == RiskLevel.SAFE

def test_distress_detected():
    assert CrisisDetector().detect("最近失眠，快撑不下去了").level == RiskLevel.DISTRESS

def test_crisis_detected():
    assert CrisisDetector().detect("我最近真的不想活了").level == RiskLevel.CRISIS

def test_imminent_detected():
    assert CrisisDetector().detect("我已经吞了两瓶安眠药").level == RiskLevel.IMMINENT

def test_empty_input_is_safe():
    assert CrisisDetector().detect("").level == RiskLevel.SAFE

def test_matched_keywords_reported():
    r = CrisisDetector().detect("我想自杀")
    assert r.level == RiskLevel.CRISIS and len(r.matched) > 0

def test_intervention_card_has_hotline():
    card = get_intervention(RiskLevel.CRISIS)
    assert card["show_card"] and "12356" in card["response"]
