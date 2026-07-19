"""
CardLoss Node — Sprint 8 (workflow), Sprint 9 (Router classification cost)

card_loss_workflow.py itself is pure Python state-machine logic — no
Claude call at any step — so every assertion here is exact-match. As
of Sprint 9, the FIRST message of each flow (the one that triggers the
workflow) now costs one classify_intent() call in the Router before
reaching this node; every subsequent step in a flow still skips the
classifier entirely, because router_node checks workflow_step > 0
before calling it. So each test below costs at most one small
classification call, not one per turn.

Each test uses its own mock user (see mock_api/mock_data.py) so a
completed "block the card" flow in one test never collides with
another test's card state within the same pytest process.
"""


def test_card_loss_full_flow(client):
    sid, uid = "test-cardloss-full", "user_002"  # single active card: card_9012, id_last4 5678

    d1 = client.post("/chat", json={
        "message": "我的卡不見了", "session_id": sid, "user_id": uid,
    }).json()
    assert d1["workflow"]["step"] == 1

    d2 = client.post("/chat", json={
        "message": "5678", "session_id": sid, "user_id": uid, "workflow": d1["workflow"],
    }).json()
    assert d2["workflow"]["step"] == 2

    d3 = client.post("/chat", json={
        "message": "1", "session_id": sid, "user_id": uid, "workflow": d2["workflow"],
    }).json()
    assert d3["workflow"]["step"] == 3

    d4 = client.post("/chat", json={
        "message": "確認", "session_id": sid, "user_id": uid, "workflow": d3["workflow"],
    }).json()
    assert d4["workflow"]["step"] == 0
    assert "掛失完成" in d4["response"]

    tickets = client.get("/tickets", params={"user_id": uid}).json()
    assert any(t["type"] == "card_loss" and t["card_id"] == "card_9012" for t in tickets)


def test_card_loss_cancel_mid_flow(client):
    sid, uid = "test-cardloss-cancel", "user_003"

    d1 = client.post("/chat", json={
        "message": "我的卡不見了", "session_id": sid, "user_id": uid,
    }).json()
    assert d1["workflow"]["step"] == 1

    d2 = client.post("/chat", json={
        "message": "取消", "session_id": sid, "user_id": uid, "workflow": d1["workflow"],
    }).json()
    assert d2["workflow"] == {"step": 0, "data": {}}
    assert "取消" in d2["response"]

    tickets = client.get("/tickets", params={"user_id": uid}).json()
    assert not any(t["type"] == "card_loss" for t in tickets)


def test_card_loss_requires_login(client):
    r = client.post("/chat", json={
        "message": "我的卡不見了", "session_id": "test-cardloss-noauth",
    })
    d = r.json()
    assert d["workflow"]["step"] == 0
    assert "登入" in d["response"]


def test_card_loss_wrong_id_last4_retries(client):
    sid, uid = "test-cardloss-wrongid", "user_002"  # real id_last4 is 5678

    d1 = client.post("/chat", json={
        "message": "我的卡不見了", "session_id": sid, "user_id": uid,
    }).json()
    assert d1["workflow"]["step"] == 1

    d2 = client.post("/chat", json={
        "message": "0000", "session_id": sid, "user_id": uid, "workflow": d1["workflow"],
    }).json()
    assert d2["workflow"]["step"] == 1  # stays on step 1, doesn't advance
    assert "剩" in d2["response"]  # "剩 N 次機會"
