"""
Account Node tool specs + dispatcher — Sprint 7 (see docs/ADR.md ADR-008).

`user_id` is intentionally NOT one of the parameters exposed to Claude:
it comes from the authenticated session (AgentState["user_id"]) and is
injected by `execute_tool`, never supplied by the model. This differs
from the generic tool params listed in docs/agent_design.md §4.2-4.4
(written for a server-side tool-calling API); here the Node layer
injects it so Claude can never be prompted into requesting another
user's account data.
"""

from ..mock_api.mock_data import get_account_balance, get_credit_card_bill
from ..mock_api.mock_data import get_transactions as _get_transactions

ACCOUNT_TOOLS = [
    {
        "name": "get_account_balance",
        "description": "Get account balance(s) for the authenticated user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_type": {
                    "type": "string",
                    "enum": ["savings", "checking", "fixed_deposit", "all"],
                    "description": "Which account to check, or 'all' for every account.",
                }
            },
        },
    },
    {
        "name": "get_credit_card_bill",
        "description": "Get credit card billing info (due amount, due date, minimum payment) for the authenticated user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {
                    "type": "string",
                    "enum": ["current_month", "last_month"],
                    "description": "Which billing cycle to check.",
                }
            },
        },
    },
    {
        "name": "get_transactions",
        "description": "Get recent transaction history for the authenticated user, most recent first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of recent transactions to return (default 5).",
                }
            },
        },
    },
]


def execute_tool(name: str, tool_input: dict, user_id: str):
    if name == "get_account_balance":
        return get_account_balance(user_id, tool_input.get("account_type", "all"))
    if name == "get_credit_card_bill":
        return get_credit_card_bill(user_id, tool_input.get("month", "current_month"))
    if name == "get_transactions":
        return _get_transactions(user_id, tool_input.get("limit", 5))
    return {"error": f"Unknown tool: {name}"}
