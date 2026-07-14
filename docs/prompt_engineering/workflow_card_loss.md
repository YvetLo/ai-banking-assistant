# Workflow Prompt — Credit Card Loss
# AI Banking Customer Assistant

**版本**：v1.0
**適用 Sprint**：Sprint 3+

---

## 流程概覽

信用卡掛失共 5 個步驟，每個步驟有獨立的 Prompt 控制對話。
關鍵設計：每步驟都有「確認後才執行」機制，避免誤操作。

```
觸發（report_card_loss）
    │
    Step 0: 告知流程
    │
    Step 1: 身分驗證（id_last4）
    │
    Step 2: 選擇要掛失的卡片
    │
    Step 3: 確認掛失（最後確認）
    │
    Step 4: 執行 + 建立 Ticket + 結束
```

---

## Step 0：觸發訊息

**觸發條件**：Router Node 判斷 intent = `report_card_loss`

**Prompt**：
```
The user wants to report a lost or stolen credit card.

Generate a response that:
1. Acknowledges their concern with empathy (card loss is stressful)
2. Explains you can help with card blocking immediately
3. Informs them you need to verify identity first (ask for last 4 digits of national ID)
4. Keeps the tone calm and reassuring

Language: {language}

Do NOT ask for any other information yet.
Do NOT mention specific card numbers yet.
```

**預期輸出（中文）**：
```
我了解卡片遺失是很緊急的情況，我馬上協助您辦理掛失。

為了保護您的帳戶安全，需要先確認您的身分。
請問您的身分證後四碼為何？
```

**預期輸出（英文）**：
```
I understand losing a card can be stressful — let me help you block it right away.

To protect your account, I need to verify your identity first.
Could you please provide the last 4 digits of your national ID?
```

---

## Step 1：身分驗證

**觸發條件**：`workflow_step = 1`，等待用戶提供 id_last4

**驗證邏輯（程式碼，非 Prompt）**：
```python
def handle_identity_verification(user_input: str, state: AgentState) -> AgentState:
    id_last4 = extract_4digits(user_input)  # 正則提取 4 位數字
    if not id_last4:
        return ask_again_state("請提供身分證後四碼（數字）")

    result = verify_identity(state["user_id"], id_last4)

    if result:
        state["workflow_step"] = 2
        state["workflow_data"]["verified"] = True
        return state  # 繼續到 Step 2
    else:
        state["workflow_data"]["verify_attempts"] = state["workflow_data"].get("verify_attempts", 0) + 1
        if state["workflow_data"]["verify_attempts"] >= 3:
            # 3 次失敗 → 轉真人
            return trigger_handoff(state, reason="identity_verification_failed")
        return ask_again_state("身分驗證未通過，請再確認後四碼")
```

**驗證失敗回應 Prompt**：
```
The user's identity verification failed. This is attempt {attempt_count} of 3.

Generate a response that:
- Gently informs them the verification did not match
- Asks them to try again (without revealing what's wrong)
- If attempt_count = 2: add a note that one more failure will require contacting customer service
- If attempt_count = 3: inform them you need to transfer to a human agent

Language: {language}
Attempt count: {attempt_count}
```

---

## Step 2：選擇卡片

**觸發條件**：`workflow_step = 2`，身分驗證通過

**資料準備（程式碼）**：
```python
user = get_user_by_id(state["user_id"])
active_cards = [card for card in user["cards"] if card["status"] == "active"]
```

**Prompt**：
```
The user's identity has been verified. Now list their active credit cards for selection.

User's Active Cards:
{cards_list}

Generate a response that:
1. Confirms identity verification was successful (brief)
2. Lists all active cards with card type and last 4 digits
3. Asks which card is lost
4. Uses numbered list for easy selection

Format for cards list:
1. VISA 白金卡 (末碼 1234)
2. Master 一般卡 (末碼 5678)

Language: {language}
```

**預期輸出（中文）**：
```
身分驗證成功！

您目前有以下信用卡，請問是哪張遺失或被盜？

1. VISA 白金卡（末碼 1234）
2. Master 一般卡（末碼 5678）

請輸入號碼（1 或 2）或直接描述卡片。
```

---

## Step 3：確認掛失（最後確認）

**觸發條件**：`workflow_step = 3`，用戶已選擇卡片

**重要設計**：執行掛失前必須最後確認，不可直接執行。

**Prompt**：
```
The user has selected the card to block. Before executing, ask for final confirmation.

Selected Card:
- Type: {card_type}
- Last 4 Digits: {card_last4}
- Card ID: {card_id}

Generate a response that:
1. Clearly states which card will be blocked
2. Warns that this action takes effect immediately and the card cannot be used
3. Asks for explicit confirmation (Yes/No or 是/否)
4. Makes it easy for user to confirm or cancel

Language: {language}
```

**預期輸出（中文）**：
```
請確認以下掛失資訊：

🔒 要掛失的卡片：VISA 白金卡（末碼 1234）

⚠️ 注意：掛失後此卡將立即停用，無法繼續消費。

請輸入「確認」繼續辦理，或輸入「取消」結束流程。
```

**用戶取消時的回應**：
```
好的，已取消掛失流程。您的 VISA 白金卡（末碼 1234）狀態不變。

如有任何問題，請撥打客服專線 0800-XXX-XXX，
或隨時告訴我您需要什麼協助。
```

---

## Step 4：執行掛失 + 建立 Ticket

**觸發條件**：`workflow_step = 4`，用戶確認

**執行順序（程式碼，非 Prompt）**：
```python
# 1. 執行掛失
block_result = block_card(state["user_id"], state["workflow_data"]["card_id"])

# 2. 建立 Ticket
ticket_result = create_ticket(
    type="card_loss",
    description=f"用戶 {state['user_id']} 申請掛失信用卡末碼 {card_last4}",
    user_id=state["user_id"],
    card_id=state["workflow_data"]["card_id"],
    priority="high"
)

# 3. 更新 state
state["workflow_data"]["blocked_at"] = block_result["blocked_at"]
state["workflow_data"]["ticket_id"] = ticket_result["ticket_id"]
state["workflow_step"] = 5  # 完成
```

**Prompt**：
```
The card has been successfully blocked and a service ticket has been created.

Block Result:
- Card: {card_type} (末碼 {card_last4})
- Blocked at: {blocked_at}

Ticket:
- Ticket ID: {ticket_id}
- Next step: Customer service will contact within 1 business day for card replacement

Generate a completion message that:
1. Confirms the card is blocked (with timestamp)
2. Provides the ticket number
3. Explains the next steps (replacement card)
4. Asks if they need anything else or want to transfer to human
5. Provides hotline number as a reference

Language: {language}
```

**預期輸出（中文）**：
```
✅ 掛失完成！

卡片資訊：VISA 白金卡（末碼 1234）
掛失時間：2026-07-15 14:32:08
服務單號：T-20260715-001

📋 後續處理：
客服人員將於 1 個工作日內與您聯繫，協助辦理補發事宜。
如需加急處理，請撥打客服專線 0800-XXX-XXX。

還有其他需要協助的嗎？或者需要立即轉接客服人員？
```

---

## 完整流程狀態機

```python
WORKFLOW_TRANSITIONS = {
    0: {"trigger": "report_card_loss",      "next": 1},
    1: {"trigger": "identity_verified",     "next": 2, "fail": "handoff"},
    2: {"trigger": "card_selected",         "next": 3},
    3: {"trigger": "user_confirmed",        "next": 4, "cancel": "end"},
    4: {"trigger": "block_executed",        "next": 5},
    5: {"trigger": "workflow_complete",     "next": "end"},
}
```

---

## 邊界情境處理

| 情境 | 處理方式 |
|------|---------|
| 用戶只有 1 張卡 | 跳過選擇步驟，直接到 Step 3 確認 |
| 用戶所有卡都已掛失 | 告知無可用卡，提供補發電話 |
| Step 1 連續 3 次驗證失敗 | 轉 Handoff Node |
| block_card API 失敗 | 告知系統暫時無法處理，緊急請電話掛失 |
| 用戶中途離開 | 未完成的 workflow state 不寫入 DB，下次重新開始 |

---

## 面試說法備忘

**問：多步驟 Workflow 的挑戰是什麼？**
> 最大挑戰是狀態管理：AI 本身無狀態，必須在每次呼叫時傳入 workflow_step 和 workflow_data，讓 AI 知道現在在流程的哪個位置。另一個挑戰是邊界情境——用戶可能在任何步驟說「取消」或「等等我先問別的」，系統需要優雅地處理流程中斷。

**問：如何確保掛失不會被誤觸發？**
> 三層保護：身分驗證（先核對身分證後四碼）、最後確認步驟（用戶必須輸入「確認」才執行）、執行後立即 Ticket 記錄（每個掛失操作都有完整 audit trail）。
