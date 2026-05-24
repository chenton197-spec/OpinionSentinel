
from app.schemas.domain import SentimentLabel

NEGATIVE_HINTS = ["投诉", "维权", "延迟", "中断", "裁员", "负面", "故障", "事故", "下滑", "翻车", "争议", "致歉", "道歉", "低俗", "问责", "处罚", "抵制", "降级", "痛批", "风波", "冒犯"]

def heuristic_sentiment(text: str) -> tuple[SentimentLabel, float, str, int]:
    lowered = text.lower()
    matched = [hint for hint in NEGATIVE_HINTS if hint in lowered]
    if matched:
        return SentimentLabel.NEGATIVE, 0.74, f"命中风险词：{'、'.join(matched)}", min(90, 55 + len(matched) * 8)
    return SentimentLabel.NEUTRAL, 0.61, "初始抓取结果，等待后续分析", 42
