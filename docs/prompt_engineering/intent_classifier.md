# Intent Classifier Prompt
# AI Banking Customer Assistant

**版本**：v1.0
**用途**：Sprint 1 起使用；此 Prompt 負責判斷用戶意圖，輸出結構化 JSON

---

## 設計思路

Intent Classification 單獨用一個 LLM 呼叫（而非在 System Prompt 中做）的理由：
1. 分類結果明確（輸出 JSON，機器可解析），不依賴 AI 在回答中暗示意圖
2. 可單獨測試、單獨計算準確率
3. 未來替換為更快的小模型（haiku → claude-haiku-4-5 已很快）不影響主對話

---

## Intent Classifier Prompt（完整版）

```
You are an intent classifier for a Taiwanese bank customer service AI.

Analyze the user's message and classify it into ONE of the following intents.
Return ONLY a valid JSON object — no explanation, no markdown, no extra text.

## Intent Categories

### FAQ Intents (no authentication required)
- credit_card_fee       — Questions about annual fees, revolving interest, cash advance, foreign transaction fees
- credit_card_benefit   — Questions about cashback, reward points, discounts, travel benefits
- account_rules         — Questions about account opening, deposit rates, maintenance fees
- transfer_rules        — Questions about transfer methods, fees, limits, international wire
- atm_service           — Questions about ATM daily limits, functions, interbank fees
- loan_info             — Questions about mortgage, personal loan products (information only)
- digital_service       — Questions about online banking, mobile app, password reset, security
- general_service       — Questions about branch hours, contact info, fee schedule, complaints

### Account Intents (authentication required)
- check_balance         — User wants to know account balance
- check_bill            — User wants to know credit card bill, due amount, due date
- check_transactions    — User wants to see recent transaction history

### Workflow Intents (authentication required)
- report_card_loss      — User reports lost or stolen credit card

### Escalation Intents
- request_human         — User explicitly requests to speak to a human agent
- complaint             — User is filing a formal complaint or expressing strong dissatisfaction

### Other
- out_of_scope          — Question is unrelated to banking services
- unclear               — Intent cannot be determined from the message

## Output Format

{
  "intent": "<intent_name>",
  "confidence": <0.0 to 1.0>,
  "language": "zh" or "en",
  "requires_auth": true or false,
  "reasoning": "<one sentence explaining the classification>"
}

## Examples

Input: 「信用卡的年費是多少？」
Output: {"intent": "credit_card_fee", "confidence": 0.98, "language": "zh", "requires_auth": false, "reasoning": "User is asking about credit card annual fee, a general FAQ."}

Input: 「我的卡不見了」
Output: {"intent": "report_card_loss", "confidence": 0.95, "language": "zh", "requires_auth": true, "reasoning": "User reports losing their card, triggering the card loss workflow."}

Input: 「你今天天氣怎樣」
Output: {"intent": "out_of_scope", "confidence": 0.99, "language": "zh", "requires_auth": false, "reasoning": "Weather is not related to banking services."}

Input: "I want to check my credit card bill"
Output: {"intent": "check_bill", "confidence": 0.97, "language": "en", "requires_auth": true, "reasoning": "User wants to check credit card billing information, requires authentication."}

## Current Message to Classify

User Message: {user_message}
Conversation Context (last 2 turns): {context}
```

---

## 在程式碼中的使用方式

```python
import anthropic
import json

client = anthropic.Anthropic()

def classify_intent(user_message: str, context: list[dict]) -> dict:
    """Classify user intent. Returns dict with intent, confidence, language, requires_auth."""

    # 取最後 2 輪對話作為 context
    recent_context = context[-4:] if len(context) >= 4 else context
    context_str = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in recent_context
    ])

    prompt = INTENT_CLASSIFIER_PROMPT.format(
        user_message=user_message,
        context=context_str or "（無對話歷史）"
    )

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        result = json.loads(response.content[0].text)
        return result
    except json.JSONDecodeError:
        # Fallback：無法解析 JSON 時的預設值
        return {
            "intent": "unclear",
            "confidence": 0.0,
            "language": "zh",
            "requires_auth": False,
            "reasoning": "Failed to parse intent classifier output"
        }
```

---

## 路由決策邏輯

```python
def route_by_intent(intent_result: dict, is_authenticated: bool) -> str:
    """Determine which node to route to based on intent classification."""

    intent = intent_result["intent"]
    confidence = intent_result["confidence"]
    requires_auth = intent_result["requires_auth"]

    # 低信心度 → 要求澄清
    if confidence < 0.6:
        return "ask_clarification"

    # 需要認證但未登入
    if requires_auth and not is_authenticated:
        return "request_login"

    # 正常路由
    routing_map = {
        # FAQ
        "credit_card_fee":    "faq_node",
        "credit_card_benefit":"faq_node",
        "account_rules":      "faq_node",
        "transfer_rules":     "faq_node",
        "atm_service":        "faq_node",
        "loan_info":          "faq_node",
        "digital_service":    "faq_node",
        "general_service":    "faq_node",
        # Account
        "check_balance":      "account_node",
        "check_bill":         "account_node",
        "check_transactions": "account_node",
        # Workflow
        "report_card_loss":   "card_loss_node",
        # Escalation
        "request_human":      "handoff_node",
        "complaint":          "handoff_node",
        # Other
        "out_of_scope":       "out_of_scope_response",
        "unclear":            "ask_clarification",
    }

    return routing_map.get(intent, "faq_node")
```

---

## 測試案例（Intent Accuracy 目標 > 90%）

| 用戶輸入 | 預期 Intent | 預期 requires_auth |
|---------|------------|-------------------|
| 「年費多少？」 | credit_card_fee | false |
| 「我的卡不見了」 | report_card_loss | true |
| 「我要看帳單」 | check_bill | true |
| 「我要投訴！服務很差！」 | complaint | false |
| 「可以幫我買股票嗎」 | out_of_scope | false |
| 「ATM 每天可以提多少？」 | atm_service | false |
| 「幫我轉帳」 | unclear | false |（轉帳是操作，不在 MVP 範圍）|
| "What's my balance?" | check_balance | true |
| "I want to speak to a human" | request_human | false |
| 「網路銀行忘記密碼怎麼辦」 | digital_service | false |
