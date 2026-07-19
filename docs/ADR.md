# Architecture Decision Record (ADR)
# AI Banking Customer Assistant

記錄每個重要技術決策的原因、取捨與生產環境方案。
面試時可逐條說明，展示設計思維的深度。

---

## ADR-001：前端使用 Streamlit 而非 Next.js

**決策日期**：2026-07-06
**狀態**：已採用

**背景**：
專案需要一個可 demo 的聊天介面，候選方案為 Next.js（React）與 Streamlit（Python）。

**決策**：選用 Streamlit

**理由**：
- 以 Python 撰寫，與後端 AI 技術棧一致，無需學習新框架
- 開發速度快（聊天介面 < 1 天），讓更多時間專注於 AI 邏輯
- 對 Python 中等程度的開發者，學習曲線極低
- Streamlit session_state 可直接管理對話記憶，不需額外狀態管理函式庫

**Trade-off**：
- UI 客製化程度低（無法做像素級設計）
- 不支援真正的多用戶並發（每個 session 獨立，無法跨 session 通訊）
- 不符合企業前端技術棧標準

**生產環境方案**：
換用 Next.js 14（App Router），後端 API 不需改動，只需更換前端呼叫方式。
聊天介面可用 Vercel AI SDK 快速實作，WebSocket 支援即時串流回覆。

---

## ADR-002：Agent 架構使用函式路由而非 LangGraph

**決策日期**：2026-07-06
**狀態**：已採用（Sprint 1-5），Sprint 6 升級

**背景**：
AI Agent 需要根據意圖路由到不同的處理模式（FAQ / Account / Workflow / Handoff）。
候選方案為 LangGraph（Graph-based State Machine）與簡單的 if/else 函式路由。

**決策**：Sprint 1-5 用函式路由，Sprint 6 重構為 LangGraph

**理由**：
- 函式路由讓每個模式的業務邏輯先跑通，確認行為正確後才重構
- LangGraph 學習曲線陡峭，若從 Day 1 使用，debug 難度大幅提高
- 先做對邏輯，再做對架構——這是企業迭代開發的正確順序
- Sprint 1-5 完成後對每個 Node 的行為已完全清楚，重構有信心

**Trade-off**：
- 函式路由可讀性佳但擴展性差，加入新意圖需修改核心邏輯
- 沒有明確的 State 管理邊界，Workflow 狀態需自行管理

**生產環境方案**：
Sprint 6 已升級為 LangGraph，各 Node 邊界清晰，State 可追蹤，
未來加入新功能（如 apply_product、dispute_transaction）只需加 Node，不影響現有邏輯。

---

## ADR-003：資料庫使用 SQLite 而非 PostgreSQL

**決策日期**：2026-07-06
**狀態**：已採用

**背景**：
系統需要儲存 Ticket 和未解決問題記錄，候選方案為 SQLite（檔案型）與 PostgreSQL（服務型）。

**決策**：選用 SQLite

**理由**：
- 無需啟動額外的資料庫服務，降低本地開發複雜度
- Python 內建 `sqlite3` 模組，零額外安裝
- 資料量小（Demo 級別），SQLite 效能完全足夠
- Schema 設計與 PostgreSQL 高度相容，切換只需更改連線字串

**Trade-off**：
- 不支援多用戶並發寫入（適合單用戶 Demo，不適合生產）
- 無內建連線池、備份機制
- 不支援 JSON 型別查詢（PostgreSQL 支援）

**切換指令**（SQLite → PostgreSQL）：
```python
# SQLite（現在）
DATABASE_URL = "sqlite:///./data.db"

# PostgreSQL（生產）
DATABASE_URL = "postgresql://user:password@localhost/banking_ai"
```
只需修改這一行，SQLAlchemy ORM 層不需改動。

---

## ADR-004：RAG 向量庫使用 FAISS 而非 ChromaDB

**決策日期**：2026-07-06
**狀態**：已採用

**背景**：
FAQ 查詢需要向量搜尋，候選方案為 FAISS（Facebook AI）與 ChromaDB。

**決策**：選用 FAISS

**理由**：
- FAISS 完全本地端，無需啟動額外服務
- 搜尋速度快，適合 Demo 規模知識庫（< 1000 chunks）
- 在 AI 社群與業界知名度高，面試官熟悉度高
- Python 安裝簡單（`pip install faiss-cpu`）

**Trade-off**：
- FAISS 不支援即時更新 index（需重建），知識庫更新需執行 rebuild 腳本
- 沒有內建 metadata 過濾功能（ChromaDB 支援）
- 不支援分散式部署

**生產環境方案**：
知識庫規模擴大後，考慮換用 ChromaDB（支援即時更新）或 Pinecone（雲端托管）。
接口設計已抽象化，切換只需修改 `rag_chain.py` 的 vector store 初始化。

---

## ADR-005：Sprint 1 使用 Context Stuffing 而非 RAG

**決策日期**：2026-07-06
**狀態**：已完成（Sprint 1），Sprint 5 升級為 RAG

**背景**：
FAQ 查詢的第一個版本，需要決定如何讓 Claude 獲得知識庫資訊。

**決策**：Sprint 1 將全部 FAQ 放入 System Prompt（Context Stuffing）

**理由**：
- 最快驗證對話邏輯是否正確，無需搭建向量資料庫
- 知識庫小時（< 5 份文件）token 數可接受
- 先確認「對話設計正確」，再確認「檢索方式正確」

**Context Stuffing 的限制（Sprint 5 升級 RAG 的原因）**：
1. FAQ 文件增加後 token 數超出限制（Claude Haiku 最大 200K tokens）
2. 無法顯示「參考來源文件」（面試加分項）
3. 無法設定 Similarity Threshold 判斷 Fallback
4. 知識庫更新需重新修改 System Prompt

**這個演進本身就是面試亮點**：
> 「我先用最簡單的方式驗證邏輯，遇到真實限制後才引入 RAG，
>  而不是一開始就過度工程化。這讓我能清楚說明 RAG 解決了什麼問題。」

---

## ADR-006：LLM 使用 Claude API 而非 OpenAI

**決策日期**：2026-07-06
**狀態**：已採用

**背景**：
系統核心 LLM 的候選方案為 Claude API（Anthropic）與 OpenAI API（GPT）。

**決策**：選用 Claude API（claude-haiku-4-5）

**理由**：
- 已有 Anthropic API Key，無需額外申請
- claude-haiku-4-5 速度快、成本低，適合 Demo 頻繁呼叫
- 支援 200K token context window，大幅降低 Context Stuffing 的限制
- 與 Claude Code 開發環境一致，技術棧統一

**Trade-off**：
- OpenAI 在業界知名度更高，部分面試官可能更熟悉 GPT API
- LangChain 對 OpenAI 的整合文件較多

**切換方式**（Claude → OpenAI）：
```python
# Claude（現在）
from anthropic import Anthropic
client = Anthropic()
response = client.messages.create(model="claude-haiku-4-5", ...)

# OpenAI（如需切換）
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(model="gpt-4o-mini", ...)
```
接口邏輯一致，切換成本低。

---

## ADR-007：中英文採用分離 FAISS Index 而非單一多語言 Index

**決策日期**：2026-07-06
**狀態**：已採用

**背景**：
系統需支援中英文雙語查詢。候選方案為：
(A) 單一多語言 embedding model + 單一 Index
(B) 語言偵測後路由到對應語言的獨立 Index

**決策**：選用方案 B（分離 Index + 語言路由）

**理由**：
- 多語言 embedding model（如 paraphrase-multilingual-mpnet-base-v2）雖支援跨語言，
  但實測中文問題常搜到英文文件（向量空間相近但語言不同），造成混淆
- 分離 Index 確保中文問題一定搜中文文件，英文問題搜英文文件
- 偵測語言後路由，邏輯清晰可維護
- 兩份知識庫各自獨立，更新互不影響

**Trade-off**：
- 需維護兩份平行的知識庫文件（中英文各一份）
- Index 建立時間 × 2，磁碟空間 × 2

**生產環境方案**：
若知識庫規模擴大，考慮使用 Cohere multilingual-v3 embedding，
其跨語言搜尋效果顯著優於 sentence-transformers，可回歸單一 Index。

---

## ADR-008：Account Node 改用 Tool-Calling 而非 Context Stuffing

**決策日期**：2026-07-17
**狀態**：已採用（Sprint 7）

**背景**：
Sprint 1-6 的帳務查詢，做法是把使用者的存款、信用卡、帳單、近期交易「全部」塞進 system prompt（`format_user_context`），FAQ 和 Account 共用同一次 Claude 呼叫（見 ADR-002 後續與 Sprint 6 design journal）。候選方案為 (A) 繼續 context stuffing，(B) Account Node 改用真正的 tool-calling，讓 Claude 依問題呼叫 `get_account_balance`／`get_credit_card_bill`／`get_transactions`。

**決策**：選用方案 B，Account Node 成為獨立於 FAQ Node 的 tool-calling Agent。

**理由**：
- Context stuffing 把使用者不相關的資料（例如只問餘額，卻把信用卡額度、帳單、交易明細全部塞進去）都送進 prompt，浪費 token 也增加模型忽略指令、幻覺的機會
- Tool-calling 讓 Claude 依實際問題決定要呼叫哪個 API，行為更貼近企業真實的 Agent 架構（呼叫核心銀行系統的真實 API，而不是把整包資料吐給 LLM）
- Node 邊界因此變得名副其實：Sprint 6 的 Account「Node」其實只是 Router 打的一個標籤，Sprint 7 之後才是真正獨立的執行單元

**安全性決策（附帶）**：
`user_id` 刻意不放進暴露給 Claude 的 tool schema，而是由 Node 層在執行工具時直接注入（見 `backend/src/agent/tools.py`）。這與 `docs/agent_design.md` §4.2-4.4 原始 tool spec（把 `user_id` 列為參數）不同——那份規格是給通用伺服器端 API 設計的；在這裡如果讓模型自己填 `user_id`，等於讓 prompt injection 有機會查詢別人的帳戶，所以改由後端注入，不信任模型輸出的身分參數。

**Trade-off**：
- 每輪對話可能需要 2 次以上的 Claude API 呼叫（先觸發 tool_use，再送 tool_result 換最終回答），延遲和成本都比 context stuffing 高
- 需要維護一個 tool-calling loop（`MAX_TOOL_ITERATIONS` 上限防止異常迴圈），比單次呼叫複雜
- Router 用關鍵字判斷 `account` vs `faq` 意圖，仍可能誤判；誤判時 FAQ Node 的 context stuffing 還留著使用者帳務資料當作安全網（見 Sprint 6 journal），行為上不會完全答不出來，只是沒有用到 tool-calling 的精準度

**生產環境方案**：
`get_account_balance` 等函式目前是讀記憶體裡的 Mock 資料，正式環境會替換成呼叫核心銀行 API（含逾時、重試、稽核 log）。Router 的關鍵字分類也建議升級為真正的 LLM Intent Classification，降低誤判率。

---

## ADR-009：Router 改用 LLM Intent Classification 而非關鍵字比對

**決策日期**：2026-07-20
**狀態**：已採用（Sprint 9）

**背景**：
`docs/agent_design.md` §3.1 從 Phase 5（Sprint 1 開始前）就把 Router 定義成「Intent Classification（LLM 分類）」，但 Sprint 1-8 實際上都是用關鍵字比對（`is_card_loss`／`is_handoff_trigger`／`is_account_query`）模擬這個行為——先把業務邏輯和 Node 邊界跑通，分類器本身留到最後再做（ADR-002／ADR-008 都預告了這一步）。候選方案為 (A) 繼續優化關鍵字清單，(B) 換成真正呼叫 Claude 做分類。

**決策**：選用方案 B，Router 改用 `backend/src/agent/intent.py` 的 `classify_intent()`。

**理由**：
- 關鍵字比對的失敗模式是結構性的，不是清單不夠長：「信用卡年費」不含 `ACCOUNT_KW` 任何字，正確落在 FAQ；但關鍵字清單完全無法處理「這張卡的年費什麼時候到期」這種語意上明顯需要個人帳務資料、卻可能誤觸發 FAQ 關鍵字比對邏輯的問題——關鍵字比對只能比對「有沒有出現特定字」，無法理解語意
- 用 `tool_choice` 強制 Claude 呼叫 `classify_intent` 這個 tool，保證每次都拿到 `faq`／`account`／`card_loss`／`handoff` 四選一的結構化結果，不需要解析自由文字、不會有「模型沒照格式回答」的例外要處理
- 這是兌現 Sprint 1 就寫好的規格，不是新增功能——對面試敘事來說，這代表「先用簡單方案讓邏輯跑通、驗證過 Node 邊界設計是對的，才引入 LLM 分類的複雜度」這個漸進式做法本身是刻意的工程判斷，不是拖到最後才想到

**Trade-off（延遲與成本）**：
- 不是每一輪都多付一次 API 呼叫：掛失流程進行中（`workflow_step > 0`）和前端強制轉真人（`force_handoff`）這兩種情況維持確定性判斷，直接跳過分類器——這兩種本質上是「系統狀態」而非「需要理解使用者說了什麼」，交給 LLM 判斷反而是多餘的不確定性來源
- 但 FAQ／Account／首次觸發掛失或轉真人，這些情境下每輪確實多了一次分類器呼叫（`max_tokens=64`，system prompt 很短），等於這幾類對話從 1 次 Claude 呼叫變成最少 2 次，延遲和成本都比純關鍵字比對高
- 分類器的準確度不是 100%——實作時第一版就踩到一個具體案例：「你搞錯了，這不是我要的答案」被誤判成 `handoff`，因為這句話本身聽起來像抱怨。修法是在 tool description 裡明確列出反例（純粹表達「答案不對／沒幫助」不算要求轉真人，仍要分類到原本主題），並用 `tests/test_router_intent.py` 把這個案例釘成一個會自動失敗的回歸測試

**生產環境方案**：
如果之後要做 §3.1 提到的「信心度低 → 反問用戶」，需要換一種呼叫方式取得信心分數（例如比較模型在拿掉 `tool_choice` 強制呼叫後會不會遲疑、或用 logprobs），目前判斷這對展示核心 Agent 架構的邊際效益不高，Sprint 9 沒有實作。

---

*最後更新：2026-07-20*
*每個 Sprint 遇到新的重要決策時，在此文件新增 ADR 條目。*
