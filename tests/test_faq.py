"""
FAQ Node — Sprint 8

These tests call the real Claude API (via the `client` session fixture),
so assertions are structural (routing, RAG sources, DB side-effects) —
never on the exact wording of an LLM-generated answer. See
docs/design_journal.md Sprint 8 entry for why response *quality* is a
manual checklist item, not a pytest assertion.
"""


def test_faq_zh_credit_card_fee(client):
    r = client.post("/chat", json={
        "message": "信用卡年費怎麼算?", "session_id": "test-faq-zh",
    })
    assert r.status_code == 200
    d = r.json()
    assert d["language"] == "zh"
    assert d["response"]
    assert any("credit_card_fees" in s for s in d["rag_sources"])


def test_faq_en_credit_card_fee(client):
    r = client.post("/chat", json={
        "message": "What is the annual fee for the credit card?", "session_id": "test-faq-en",
    })
    assert r.status_code == 200
    d = r.json()
    assert d["language"] == "en"
    assert d["response"]
    assert any("credit_card_fees" in s for s in d["rag_sources"])


def test_negative_feedback_and_low_similarity_dual_log(client):
    """
    Regression test for the Sprint 6 edge case: a single turn can fire
    BOTH the negative-feedback log entry and the RAG low-similarity log
    entry. Sprint 6 deliberately preserved this "one turn, two log rows"
    behavior from the original if/else handler.
    """
    sid = "test-faq-dual-log"
    r = client.post("/chat", json={
        "message": "你搞錯了，這不是我要的答案", "session_id": sid,
    })
    assert r.status_code == 200
    assert r.json()["is_negative_feedback"] is True

    unresolved = client.get("/unresolved", params={"limit": 100}).json()
    reasons = {u["trigger_reason"] for u in unresolved if u["session_id"] == sid}
    assert "negative_feedback" in reasons
    assert "rag_low_similarity" in reasons
