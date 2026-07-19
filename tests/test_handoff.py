"""
Handoff Node — Sprint 8

handoff_node returns a hardcoded template (prompts.HANDOFF_MSG) — no
Claude call — so these tests cost zero tokens and assert exact
equality.
"""

from backend.src.prompts import HANDOFF_MSG


def test_handoff_keyword_trigger(client):
    sid = "test-handoff-keyword"
    r = client.post("/chat", json={"message": "我要投訴", "session_id": sid})
    assert r.status_code == 200
    assert r.json()["response"] == HANDOFF_MSG["zh"]

    unresolved = client.get("/unresolved", params={"limit": 100}).json()
    matching = [u for u in unresolved if u["session_id"] == sid]
    assert any(u["trigger_reason"] == "handoff_keyword" for u in matching)


def test_handoff_force_flag(client):
    """Frontend sets force_handoff=True once fallback_count hits the
    threshold, independent of keyword matching."""
    r = client.post("/chat", json={
        "message": "隨便問個問題", "session_id": "test-handoff-force", "force_handoff": True,
    })
    assert r.status_code == 200
    assert r.json()["response"] == HANDOFF_MSG["zh"]
