"""
Mock customer data — simulates CRM / Core Banking API responses.
All data is entirely fictional and for demo purposes only.
"""

from datetime import datetime

MOCK_USERS = {
    "user_001": {
        "user_id": "user_001",
        "username": "demo_user1",
        "password": "demo1234",
        "name": "陳小明 / Chen Xiao-Ming",
        "id_last4": "1234",
        "email": "lisa.chen@example.com",
        "phone": "0912-XXX-001",
        "accounts": {
            "savings": {
                "account_no": "012-XXX-000001",
                "balance": 85000,
                "currency": "TWD"
            },
            "checking": {
                "account_no": "012-XXX-000002",
                "balance": 12000,
                "currency": "TWD"
            }
        },
        "cards": [
            {
                "card_id": "card_1234",
                "last4": "1234",
                "type": "VISA 白金卡 / VISA Platinum",
                "status": "active",
                "credit_limit": 300000,
                "available_credit": 245000
            },
            {
                "card_id": "card_5678",
                "last4": "5678",
                "type": "Master 一般卡 / Master Standard",
                "status": "active",
                "credit_limit": 100000,
                "available_credit": 82500
            }
        ],
        "bill": {
            "current_month": {
                "due_amount": 12450,
                "due_date": "2026-07-25",
                "min_payment": 3500,
                "statement_date": "2026-07-03"
            },
            "last_month": {
                "due_amount": 8230,
                "due_date": "2026-06-25",
                "min_payment": 2500,
                "paid": True,
                "paid_date": "2026-06-20"
            }
        },
        "recent_transactions": [
            {"date": "2026-07-10", "description": "家樂福 Carrefour", "amount": -3200, "category": "Shopping"},
            {"date": "2026-07-08", "description": "誠品書店 Eslite", "amount": -850, "category": "Books"},
            {"date": "2026-07-05", "description": "薪資轉入 Salary", "amount": 65000, "category": "Income"},
            {"date": "2026-07-03", "description": "Netflix", "amount": -390, "category": "Entertainment"},
            {"date": "2026-06-28", "description": "全聯超市 PX Mart", "amount": -1560, "category": "Groceries"},
        ]
    },

    "user_002": {
        "user_id": "user_002",
        "username": "demo_user2",
        "password": "demo5678",
        "name": "王大明 / Wang Da-Ming",
        "id_last4": "5678",
        "email": "kevin.wang@example.com",
        "phone": "0923-XXX-002",
        "accounts": {
            "savings": {
                "account_no": "012-XXX-000003",
                "balance": 320000,
                "currency": "TWD"
            }
        },
        "cards": [
            {
                "card_id": "card_9012",
                "last4": "9012",
                "type": "VISA 無限卡 / VISA Infinite",
                "status": "active",
                "credit_limit": 1000000,
                "available_credit": 780000
            }
        ],
        "bill": {
            "current_month": {
                "due_amount": 58900,
                "due_date": "2026-07-25",
                "min_payment": 15000,
                "statement_date": "2026-07-03"
            },
            "last_month": {
                "due_amount": 42300,
                "due_date": "2026-06-25",
                "min_payment": 12000,
                "paid": True,
                "paid_date": "2026-06-18"
            }
        },
        "recent_transactions": [
            {"date": "2026-07-12", "description": "新加坡航空 Singapore Airlines", "amount": -28000, "category": "Travel"},
            {"date": "2026-07-10", "description": "台北喜來登 Sheraton Taipei", "amount": -15600, "category": "Hotel"},
            {"date": "2026-07-08", "description": "餐廳消費 Dining", "amount": -3800, "category": "Dining"},
            {"date": "2026-07-05", "description": "薪資轉入 Salary", "amount": 120000, "category": "Income"},
        ]
    },

    "user_003": {
        "user_id": "user_003",
        "username": "demo_user3",
        "password": "demo9999",
        "name": "陳春花 / Chen Chun-Hua",
        "id_last4": "9999",
        "email": "grandma.chen@example.com",
        "phone": "0934-XXX-003",
        "accounts": {
            "savings": {
                "account_no": "012-XXX-000005",
                "balance": 450000,
                "currency": "TWD"
            },
            "fixed_deposit": {
                "account_no": "012-XXX-000006",
                "balance": 1000000,
                "currency": "TWD",
                "maturity_date": "2027-01-15",
                "interest_rate": "1.75%"
            }
        },
        "cards": [
            {
                "card_id": "card_3456",
                "last4": "3456",
                "type": "Master 金卡 / Master Gold",
                "status": "active",
                "credit_limit": 80000,
                "available_credit": 72000
            }
        ],
        "bill": {
            "current_month": {
                "due_amount": 4320,
                "due_date": "2026-07-25",
                "min_payment": 1296,
                "statement_date": "2026-07-03"
            },
            "last_month": {
                "due_amount": 3890,
                "due_date": "2026-06-25",
                "min_payment": 1167,
                "paid": True,
                "paid_date": "2026-06-22"
            }
        },
        "recent_transactions": [
            {"date": "2026-07-11", "description": "全聯超市 PX Mart", "amount": -2100, "category": "Groceries"},
            {"date": "2026-07-09", "description": "藥局 Pharmacy", "amount": -680, "category": "Health"},
            {"date": "2026-07-05", "description": "退休俸轉入 Pension", "amount": 38000, "category": "Income"},
            {"date": "2026-07-02", "description": "7-Eleven", "amount": -245, "category": "Convenience Store"},
        ]
    }
}


def get_user_by_credentials(username: str, password: str) -> dict | None:
    """Authenticate user by username and password."""
    for user in MOCK_USERS.values():
        if user["username"] == username and user["password"] == password:
            return {k: v for k, v in user.items() if k != "password"}
    return None


def get_user_by_id(user_id: str) -> dict | None:
    """Get user data by user_id."""
    user = MOCK_USERS.get(user_id)
    if user:
        return {k: v for k, v in user.items() if k != "password"}
    return None


def verify_identity(user_id: str, id_last4: str) -> bool:
    """Verify user identity by ID number last 4 digits."""
    user = MOCK_USERS.get(user_id)
    if not user:
        return False
    return user["id_last4"] == id_last4


def get_card_by_id(user_id: str, card_id: str) -> dict | None:
    """Get a specific card belonging to a user."""
    user = MOCK_USERS.get(user_id)
    if not user:
        return None
    for card in user.get("cards", []):
        if card["card_id"] == card_id:
            return card
    return None


def get_account_balance(user_id: str, account_type: str = "all") -> dict:
    """Get account balance(s). account_type: savings/checking/fixed_deposit/all."""
    user = MOCK_USERS.get(user_id)
    if not user:
        return {"error": "User not found"}
    accounts = user.get("accounts", {})
    if account_type == "all":
        return accounts
    if account_type in accounts:
        return {account_type: accounts[account_type]}
    return {"error": f"No {account_type} account found for this user"}


def get_credit_card_bill(user_id: str, month: str = "current_month") -> dict:
    """Get credit card billing info. month: current_month/last_month."""
    user = MOCK_USERS.get(user_id)
    if not user:
        return {"error": "User not found"}
    bill = user.get("bill", {}).get(month)
    if bill is None:
        return {"error": f"No bill data for {month}"}
    return bill


def get_transactions(user_id: str, limit: int = 5) -> list[dict]:
    """Get recent transaction history, most recent first."""
    user = MOCK_USERS.get(user_id)
    if not user:
        return []
    return user.get("recent_transactions", [])[:limit]


def block_card(user_id: str, card_id: str) -> dict:
    """Block (report lost) a credit card. Returns result."""
    user = MOCK_USERS.get(user_id)
    if not user:
        return {"success": False, "error": "User not found"}

    for card in user.get("cards", []):
        if card["card_id"] == card_id:
            card["status"] = "blocked"
            return {
                "success": True,
                "card_id": card_id,
                "last4": card["last4"],
                "blocked_at": datetime.now().isoformat()
            }
    return {"success": False, "error": "Card not found"}
