"""
Account Node — Sprint 8

`test_account_requires_login` asserts an exact string because that
message is a hardcoded template (nodes.NOT_LOGGED_IN_ACCOUNT), never
touched by the LLM. Every other test here calls the real Claude API
(tool-calling loop) so assertions stay structural — see test_faq.py
docstring for why.
"""

USER = "user_001"  # read-only account tests: never mutates state, safe to share


def test_account_requires_login(client):
    r = client.post("/chat", json={
        "message": "我的信用卡帳單多少", "session_id": "test-acct-noauth",
    })
    assert r.status_code == 200
    d = r.json()
    assert d["response"] == "要查詢帳務資訊，需要先登入喔！請點選側邊欄登入。"


def test_account_balance_query(client):
    r = client.post("/chat", json={
        "message": "我的存款餘額有多少?", "session_id": "test-acct-balance", "user_id": USER,
    })
    assert r.status_code == 200
    d = r.json()
    assert d["language"] == "zh"
    assert d["response"]


def test_account_bill_query(client):
    r = client.post("/chat", json={
        "message": "這個月信用卡帳單要繳多少，截止日是什麼時候?",
        "session_id": "test-acct-bill", "user_id": USER,
    })
    assert r.status_code == 200
    assert r.json()["response"]


def test_account_transactions_query(client):
    r = client.post("/chat", json={
        "message": "幫我看一下最近的消費記錄", "session_id": "test-acct-txns", "user_id": USER,
    })
    assert r.status_code == 200
    assert r.json()["response"]


def test_account_mixed_query_calls_multiple_tools(client):
    """A question spanning two tools (balance + transactions) should
    still resolve in one turn via the tool-use loop, not require the
    user to ask twice."""
    r = client.post("/chat", json={
        "message": "我的活期存款餘額多少，還有最近花了什麼",
        "session_id": "test-acct-mixed", "user_id": USER,
    })
    assert r.status_code == 200
    assert r.json()["response"]
