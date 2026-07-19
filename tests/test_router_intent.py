"""
Router intent classification — Sprint 9

Calls classify_intent() directly rather than through /chat, since it's
tested as a pure classification unit — no need to also pay for the
downstream FAQ/Account/CardLoss answering call just to check routing.
"""

from backend.main import client, MODEL
from backend.src.agent.intent import classify_intent


def test_classifies_general_question_as_faq():
    assert classify_intent(client, MODEL, "信用卡年費怎麼算?") == "faq"


def test_classifies_personal_account_question_as_account():
    assert classify_intent(client, MODEL, "我這個月信用卡帳單多少?") == "account"


def test_classifies_lost_card_as_card_loss():
    assert classify_intent(client, MODEL, "我的卡不見了") == "card_loss"


def test_classifies_explicit_human_request_as_handoff():
    assert classify_intent(client, MODEL, "我要投訴") == "handoff"


def test_negative_feedback_not_misrouted_to_handoff():
    """Regression guard: general dissatisfaction with an answer should
    stay faq/account (logged separately as negative_feedback inside the
    QA node), NOT escalate straight to Handoff."""
    assert classify_intent(client, MODEL, "你搞錯了，這不是我要的答案") != "handoff"
