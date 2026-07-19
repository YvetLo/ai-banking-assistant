"""
Handoff Node — Sprint 8

handoff_node itself returns a hardcoded template (prompts.HANDOFF_MSG)
— no Claude call there — so the response text is asserted exactly.
As of Sprint 9, reaching this node via keyword-style intent (rather
than force_handoff) costs one small classify_intent() call in the
Router — see test_router_intent.py for why that trade was made.
force_handoff still bypasses the classifier entirely (checked before
classify_intent in router_node), so that path stays zero-cost.
"""

from backend.src.prompts import HANDOFF_MSG


def test_handoff_explicit_request(client):
    sid = "test-handoff-keyword"
    r = client.post("/chat", json={"message": "我要投訴", "session_id": sid})
    assert r.status_code == 200
    assert r.json()["response"] == HANDOFF_MSG["zh"]

    unresolved = client.get("/unresolved", params={"limit": 100}).json()
    matching = [u for u in unresolved if u["session_id"] == sid]
    assert any(u["trigger_reason"] == "handoff_intent" for u in matching)


def test_handoff_force_flag(client):
    """Frontend sets force_handoff=True once fallback_count hits the
    threshold — this must bypass the classifier entirely, not just
    happen to agree with it."""
    r = client.post("/chat", json={
        "message": "隨便問個問題", "session_id": "test-handoff-force", "force_handoff": True,
    })
    assert r.status_code == 200
    assert r.json()["response"] == HANDOFF_MSG["zh"]
