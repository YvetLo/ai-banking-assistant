"""
Lightweight language/intent helpers shared by the LangGraph Router Node.
Sprint 1-4 validated these as inline keyword checks in main.py;
Sprint 6 moved them here unchanged so the Router Node can import them.
"""

import re

from langdetect import detect, LangDetectException

CARD_LOSS_KW = ["掛失", "遺失", "不見了", "被偷", "lost card", "card lost", "stolen card", "block my card"]
HANDOFF_KW = ["投訴", "申訴", "真人", "客服人員", "我要告", "complaint", "speak to agent", "speak to human", "human agent", "real person"]
NEGATIVE_KW = ["不對", "不是", "沒幫助", "幫不上", "沒有回答", "不是這樣", "還是不懂", "你搞錯了",
               "wrong", "not helpful", "not what i asked", "didn't answer", "useless", "that's not right"]
ACCOUNT_KW = ["餘額", "帳單", "交易", "明細", "消費", "額度", "存款", "活期", "定存",
              "balance", "bill", "statement", "transaction", "credit limit"]


def detect_language(text: str) -> str:
    if re.search(r"[一-鿿㐀-䶿]", text):
        return "zh"
    try:
        return "zh" if detect(text) in ("zh-tw", "zh-cn", "zh") else "en"
    except LangDetectException:
        return "zh"


def is_card_loss(text: str) -> bool:
    return any(kw in text.lower() for kw in CARD_LOSS_KW)


def is_handoff_trigger(text: str) -> bool:
    return any(kw in text.lower() for kw in HANDOFF_KW)


def is_negative_feedback(text: str) -> bool:
    return any(kw in text.lower() for kw in NEGATIVE_KW)


def is_account_query(text: str) -> bool:
    return any(kw in text.lower() for kw in ACCOUNT_KW)
