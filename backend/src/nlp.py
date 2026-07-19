"""
Lightweight language/feedback helpers.

Sprint 1-4 validated CARD_LOSS_KW/HANDOFF_KW/ACCOUNT_KW keyword
matching as inline checks in main.py; Sprint 6 moved them here
unchanged; Sprint 9 replaced them with a real LLM classifier
(backend/src/agent/intent.py) and removed them. NEGATIVE_KW stays —
it's a separate concern (logging negative feedback for review inside
the FAQ/Account Node), not routing.
"""

import re

from langdetect import detect, LangDetectException

NEGATIVE_KW = ["不對", "不是", "沒幫助", "幫不上", "沒有回答", "不是這樣", "還是不懂", "你搞錯了",
               "wrong", "not helpful", "not what i asked", "didn't answer", "useless", "that's not right"]


def detect_language(text: str) -> str:
    if re.search(r"[一-鿿㐀-䶿]", text):
        return "zh"
    try:
        return "zh" if detect(text) in ("zh-tw", "zh-cn", "zh") else "en"
    except LangDetectException:
        return "zh"


def is_negative_feedback(text: str) -> bool:
    return any(kw in text.lower() for kw in NEGATIVE_KW)
