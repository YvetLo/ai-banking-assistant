# AI Agent Design
# AI Banking Customer Assistant

**版本**：v1.1
**對應 Sprint**：Sprint 6（LangGraph 架構）、Sprint 7（Account Node tool-calling），Sprint 1-5 使用函式路由（if/else）模擬相同行為

---

## 1. 設計原則

本文件定義 AI Agent 的完整行為規格。Sprint 1-5 以 if/else 函式路由實作，Sprint 6 將重構為 LangGraph State Machine，兩者的外部行為一致，差異只在內部架構。

**為什麼先用函式路由再升級？**（詳見 ADR.md ADR-02）
> 先讓業務邏輯跑通，再引入框架複雜度。函式路由清晰易 debug，LangGraph 提供可追蹤的 State 和可組合的 Node，適合作最終展示架構。

---

## 2. Agent State 定義

```python
from typing import TypedDict, Optional

class AgentState(TypedDict):
    # 對話歷史（最多 10 輪，rolling window）
    messages: list[dict]          # {"role": "user"/"assistant", "content": str}

    # 意圖與語言
    intent: str                   # credit_card_fee / check_bill / report_card_loss / ...
    language: str                 # "zh" or "en"

    # 身分認證
    user_authenticated: bool
    user_id: Optional[str]        # 登入後設定

    # 多步驟 Workflow（信用卡掛失）
    workflow_step: int            # 0=未開始, 1=身分驗證, 2=選卡片, 3=確認掛失, 4=完成
    workflow_data: dict           # {"card_id": ..., "id_last4": ..., "ticket_id": ...}

    # Fallback 追蹤
    fallback_count: int           # 連續 fallback 次數，達 3 次觸發 Human Handoff

    # Session 管理
    session_id: str               # UUID，每次對話開始時生成
    rag_context: list[dict]       # RAG 搜尋結果 [{"source": ..., "text": ...}]
```

---

## 3. Node 設計

### 3.1 Router Node（意圖路由）

**職責**：分析用戶輸入，判斷意圖類型，路由到對應 Node。

**輸入**：user message + conversation history
**輸出**：更新 `state.intent` 和 `state.language`，決定下一個 Node

**路由邏輯**：

```
用戶輸入
    │
    ▼
langdetect → state.language = "zh" or "en"
    │
    ▼
Intent Classification（LLM 分類）
    │
    ├── FAQ 類 → FAQ Node
    │   (credit_card_fee, account_rules, loan_info, digital_service, general_service)
    │
    ├── ACCOUNT 類 → Account Node（需登入）
    │   (check_balance, check_bill, check_transactions)
    │
    ├── WORKFLOW 類 → CardLoss Node（需登入）
    │   (report_card_loss)
    │
    └── ESCALATION 類 → Handoff Node
        (request_human, complaint)
```

**Fallback 條件**：
- 意圖分類信心度低 → 反問用戶（最多 2 次）
- 連續 3 次無法解決 → 強制觸發 Handoff Node

---

### 3.2 FAQ Node（知識庫查詢）

**職責**：使用 RAG 搜尋知識庫，生成回答。

**Sprint 1-4**：Context Stuffing（把所有 FAQ 塞進 System Prompt）
**Sprint 5+**：FAISS RAG（Top-K=3 chunk 搜尋，附來源文件）

**輸入**：user query + `state.language`
**輸出**：回答文字 + 來源文件（Sprint 5 起）

**執行步驟**：
1. 呼叫 `search_knowledge_base(query, language, top_k=3)`
2. similarity score < 0.7 → 判定 Fallback
3. 呼叫 Claude API，帶入 context chunks
4. 如為貸款相關意圖，強制插入 Disclaimer
5. 更新 `state.messages`，記錄回答

**Fallback 處理**：
- 誠實告知「知識庫目前無此資訊」
- 提供客服電話：0800-XXX-XXX
- 呼叫 `log_unresolved(query, reason="low_similarity", ...)`

---

### 3.3 Account Node（帳務查詢）— Sprint 7 起為真正 tool-calling

**職責**：驗證登入狀態，呼叫 Mock Banking API，整理成自然語言。

**先決條件**：`state.user_authenticated == True`
若未登入 → Node 內直接回傳登入提示，不呼叫 Claude / 不執行任何 tool

**支援意圖**：

| 意圖 | 呼叫 Tool | 回傳資料 |
|------|-----------|---------|
| check_balance | `get_account_balance` | 帳戶餘額 |
| check_bill | `get_credit_card_bill` | 應繳金額、截止日、最低應繳 |
| check_transactions | `get_transactions` | 近期交易明細列表 |

**實作備註（Sprint 7）**：`user_id` 不放進 Claude 看得到的 tool schema，由 `backend/src/agent/tools.py` 的 `execute_tool()` 在後端注入，避免模型被誘導查詢其他使用者的帳戶（詳見 ADR-008）。一輪對話最多允許 `MAX_TOOL_ITERATIONS=3` 次 tool-calling 迴圈，超過則回覆客服專線並記錄 `trigger_reason="tool_loop_exceeded"`。

**輸出格式**（LLM 整理後）：
```
您本月信用卡應繳金額為 NT$12,450
繳款截止日：2026-07-25
最低應繳：NT$3,500

需要查詢消費明細嗎？
```

---

### 3.4 CardLoss Workflow Node（信用卡掛失）

**職責**：執行多步驟掛失流程，每步都需用戶確認。

**先決條件**：需登入（或在流程中完成身分驗證）

**流程步驟**（`state.workflow_step`）：

```
Step 0: 觸發
  Bot: 「我可以協助您辦理信用卡掛失。為保護您的帳戶安全，
        需要先確認您的身分，請問您的身分證後四碼為何？」

Step 1: 身分驗證
  User: 提供 id_last4
  Tool: verify_identity(user_id, id_last4)
  ✅ 通過 → Step 2
  ❌ 失敗 → 最多 3 次，失敗後轉 Handoff

Step 2: 選擇卡片
  Bot: 列出用戶所有信用卡（card_id, last4, type）
  User: 選擇遺失的卡片
  Tool: get_card_by_id(user_id, card_id)

Step 3: 確認掛失
  Bot: 「確認要掛失末碼 XXXX 的 VISA 白金卡嗎？
        掛失後此卡將立即停用，無法繼續使用。（是/否）」
  User: 確認

Step 4: 執行掛失 + 建立 Ticket
  Tool: block_card(user_id, card_id)
  Tool: create_ticket(type="card_loss", user_id, card_id)
  Bot: 「✅ 掛失完成！
        卡號末碼 XXXX 已鎖定（2026-07-15 14:32）
        服務單號：T-20260715-001
        客服將於 1 個工作日聯繫您處理補發事宜。
        需要立即轉接客服人員嗎？」
```

**中途放棄處理**：
- 用戶說「算了」「取消」→ 詢問確認後結束流程
- Workflow 未完成的 state 不寫入 DB

---

### 3.5 Handoff Node（轉真人客服）

**職責**：結束 AI 對話，引導用戶轉接真人客服。

**觸發條件**：
1. 用戶主動要求：「我要真人」「投訴」「申訴」"speak to agent" "complaint"
2. 連續 3 次 Fallback（`state.fallback_count >= 3`）
3. Workflow 中用戶明確要求
4. 涉及金額爭議 > NT$10,000 的描述

**回應模板**：
```
很抱歉我沒能完全解決您的問題。

📞 客服專線：0800-XXX-XXX
   服務時間：週一至週五 08:00–22:00

🌐 線上客服（24小時）：官網右下角聊天按鈕

如您需要緊急服務（卡片掛失、帳戶凍結），
請撥打客服專線並選擇「緊急服務」，全天候有真人接聽。

本次對話將記錄供客服人員參考，感謝您的耐心。
```

**後置動作**：
- 呼叫 `log_unresolved(trigger_reason="handoff", ...)`
- 記錄 session_id 供客服查詢

---

### 3.6 Logger Node（記錄未解決）

**職責**：將 Fallback 和 Handoff 事件寫入 SQLite `unresolved_queries` 表。

不直接回應用戶，僅後置執行。

**記錄欄位**：
```python
{
    "session_id": state["session_id"],
    "user_query": original_user_message,
    "language": state["language"],
    "intent": state["intent"],
    "trigger_reason": "low_similarity" | "handoff" | "api_failure",
    "similarity_score": float or None,
    "created_at": datetime.now()
}
```

---

## 4. Tool 定義規格

符合 OpenAI-compatible tool spec 格式，Claude API 可直接使用。

### 4.1 search_knowledge_base
```json
{
  "name": "search_knowledge_base",
  "description": "Search the FAQ knowledge base using vector similarity. Returns top-K relevant chunks.",
  "parameters": {
    "query": {"type": "string", "description": "User's question"},
    "language": {"type": "string", "enum": ["zh", "en"]},
    "top_k": {"type": "integer", "default": 3}
  }
}
```

### 4.2 get_account_balance
```json
{
  "name": "get_account_balance",
  "description": "Get account balance for authenticated user.",
  "parameters": {
    "user_id": {"type": "string"},
    "account_type": {"type": "string", "enum": ["savings", "checking", "fixed_deposit", "all"]}
  }
}
```

### 4.3 get_credit_card_bill
```json
{
  "name": "get_credit_card_bill",
  "description": "Get credit card billing info (due amount, due date, min payment).",
  "parameters": {
    "user_id": {"type": "string"},
    "month": {"type": "string", "description": "current_month or last_month", "default": "current_month"}
  }
}
```

### 4.4 get_transactions
```json
{
  "name": "get_transactions",
  "description": "Get recent transaction history for authenticated user.",
  "parameters": {
    "user_id": {"type": "string"},
    "limit": {"type": "integer", "default": 5, "description": "Number of recent transactions"}
  }
}
```

### 4.5 verify_identity
```json
{
  "name": "verify_identity",
  "description": "Verify user identity using last 4 digits of national ID.",
  "parameters": {
    "user_id": {"type": "string"},
    "id_last4": {"type": "string", "description": "Last 4 digits of national ID"}
  }
}
```

### 4.6 block_card
```json
{
  "name": "block_card",
  "description": "Block (report lost) a credit card. Immediately disables the card.",
  "parameters": {
    "user_id": {"type": "string"},
    "card_id": {"type": "string"}
  }
}
```

### 4.7 create_ticket
```json
{
  "name": "create_ticket",
  "description": "Create a service ticket (card loss, complaint, general inquiry).",
  "parameters": {
    "type": {"type": "string", "enum": ["card_loss", "complaint", "general"]},
    "description": {"type": "string"},
    "user_id": {"type": "string", "nullable": true},
    "card_id": {"type": "string", "nullable": true},
    "priority": {"type": "string", "enum": ["high", "normal"], "default": "normal"}
  }
}
```

### 4.8 escalate_to_human
```json
{
  "name": "escalate_to_human",
  "description": "Trigger human handoff. Logs session and returns handoff message.",
  "parameters": {
    "reason": {"type": "string", "description": "Why handoff was triggered"},
    "session_id": {"type": "string"}
  }
}
```

### 4.9 log_unresolved
```json
{
  "name": "log_unresolved",
  "description": "Log an unresolved query to the database for human review.",
  "parameters": {
    "user_query": {"type": "string"},
    "language": {"type": "string", "enum": ["zh", "en"]},
    "intent": {"type": "string"},
    "trigger_reason": {"type": "string", "enum": ["low_similarity", "handoff", "api_failure", "tool_loop_exceeded"]},
    "session_id": {"type": "string"},
    "similarity_score": {"type": "number", "nullable": true}
  }
}
```

---

## 5. Node 執行流程圖（LangGraph）

```
START
  │
  ▼
Router Node
  │
  ├── intent=FAQ          → FAQ Node ──────────┐
  │                                             │
  ├── intent=ACCOUNT      → Account Node ───────┤
  │   (need auth)                               │
  ├── intent=WORKFLOW     → CardLoss Node ──────┤
  │   (need auth)                               │
  └── intent=ESCALATION   → Handoff Node ───────┤
                                                │
         ┌──────────────────────────────────────┘
         │
         ▼
    Logger Node（如有 Fallback / Handoff）
         │
         ▼
        END
```

---

## 6. Sprint 實作路線圖

| Sprint | 實作方式 | Node 行為 |
|--------|---------|-----------|
| Sprint 1 | 函式路由 + Context Stuffing | Router → FAQ（用 System Prompt 內嵌 FAQ）|
| Sprint 2 | 函式路由 + Mock API | + Account Node |
| Sprint 3 | 函式路由 + SQLite | + CardLoss Node（基本版）|
| Sprint 4 | 函式路由 + 觸發偵測 | + Handoff Node + Logger Node |
| Sprint 5 | 函式路由 + FAISS | FAQ Node 升級為真正 RAG |
| Sprint 6 | **LangGraph 重構** | 所有 Node 遷移為 LangGraph Graph |
| Sprint 7 | **Account tool-calling** | Account Node 改為真正呼叫 `get_account_balance`／`get_credit_card_bill`／`get_transactions`，不再與 FAQ 共用 context stuffing |

---

## 7. 面試說法備忘

**問：為什麼要用 LangGraph？**
> Sprint 1-5 的函式路由已驗證所有業務邏輯。LangGraph 提供三個好處：State 顯式追蹤（每個 Node 的輸入輸出可 log）、Node 邊界明確（新增功能不破壞現有邏輯）、條件邊（Conditional Edge）讓路由邏輯從 if/else 變成宣告式定義，更易維護。

**問：Workflow 中斷怎麼辦？**
> v1 不支援斷點續連，流程中途關閉需重新開始。生產環境的解法是把 `workflow_step` 和 `workflow_data` 存入 Redis（TTL 30 分鐘），重新連線時恢復流程狀態。

**問：同時支援多少用戶？**
> Demo 版本為單用戶展示。生產環境加入 Rate Limiting（每用戶每分鐘限 10 次呼叫）、FAQ 回答 Redis 快取（相同問題不重複呼叫 Claude API）、水平擴展（多個 FastAPI instance + Load Balancer）。

**問：FAQ Node 和 Account Node 是不是真的兩個獨立節點？**
> Sprint 6 剛重構完的時候不是——兩者共用同一個函式（`qa_node`），因為 Sprint 1-5 驗證過的行為就是 system prompt 同時帶 RAG chunks 和帳務資料，拆成兩次真正獨立的 LLM 呼叫會改變外部行為，違反那次重構「只換架構、不換行為」的前提。這是刻意先欠的技術債，不是沒想到。Sprint 7 把這筆債還了：Account Node 現在是獨立的 tool-calling Agent，只在真正需要帳務資料時才呼叫對應的 tool，FAQ Node 的 context stuffing 則保留下來當作 Router 誤判時的安全網（詳見 ADR-008、Sprint 7 design journal）。
