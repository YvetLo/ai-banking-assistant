# 設計決策日誌 Design Decision Journal
# AI Banking Customer Assistant

**說明**：這份日誌記錄整個專案的思考過程，從需求發現到最終反思，
按照四個維度循環記錄每個 Phase 和 Sprint 的決策歷程。

與 `ADR.md` 的區別：
- **ADR.md** → 記錄技術選型的正式決策（What & Why，結構化）
- **Design Journal** → 記錄人的思考過程（How I thought, What I learned，敘述性）

---

## 格式說明

每個 Phase / Sprint 包含四個區塊：

> **① Requirement & Discovery** — 為什麼做、解決什麼問題、目標使用者是誰
> **② Design Decision** — 遇到哪些選擇、有哪些方案、最後為什麼這樣決定
> **③ Implementation & Iteration** — 實作後遇到什麼問題、如何修改
> **④ Evaluation & Reflection** — 測試結果如何、哪些地方有效、哪些地方下一版需要改善

---
---

# Phase 1：Product Discovery

## ① Requirement & Discovery

**為什麼做這個專案？**
我目前沒有在工作，需要一個具體的 AI 作品集展示實作能力。銀行客服是很好的選題，因為它涵蓋了 AI 工程最常見的三種模式：知識庫查詢（RAG）、API 整合、多步驟工作流程（Workflow），一個專案就能展示多種能力。

**解決什麼問題？**
銀行客服中心每日處理大量重複性查詢，造成等待時間長、人力成本高。AI 助理可以自動處理 80% 的標準問題，讓真人客服專注於複雜案件。

**目標使用者是誰？**
設計了三個 Persona：
- **Lisa（25-35 歲，上班族）**：下班後查帳單，不想等電話
- **Kevin（商務人士）**：出差時緊急掛失，需要即時處理
- **陳伯伯（銀髮族）**：需要清楚的步驟引導，不熟悉複雜操作

這三個 Persona 剛好對應三種不同的使用強度和技術熟練度，幫助我設計出包容性更廣的對話流程。

## ② Design Decision

**三個 MVP 的選擇邏輯：**
- **FAQ 查詢**：佔客服量約 60%，是最高頻的需求，且不需登入，最容易驗證
- **帳務查詢**：需要個人資料，代表 API 整合能力，是企業 AI 最常見的場景
- **信用卡掛失**：雖然量少，但影響最大（緊急性高），代表多步驟 Workflow 能力

最初考慮是否要加入「產品申辦」，後來決定不加，原因是申辦流程複雜度高、需要更多產品知識，對作品集的額外價值有限。先把三個 MVP 做好，比四個 MVP 做一半更有說服力。

**Disclaimer 設計的思考：**
一開始沒有想到這個問題。被挑戰「AI 回答錯誤利率，責任在誰？」之後，設計了三層防護：UI 固定文字、Prompt 規則、Intent 層強制插入。這個設計過程本身就是面試時可以說的故事。

## ③ Implementation & Iteration

*（本階段為文件產出，無實作內容）*

## ④ Evaluation & Reflection

**有效的部分：**
- PRD 的 12 個章節涵蓋了 PM 面試官會問的大部分問題
- 三個 Persona 的設計讓對話流程更有針對性
- Success Metrics 把「感覺上有效」轉換成可量化的數字

**下一版需要改善：**
- Use Case 可以加入更多的 Edge Case 場景描述
- 銀行業的監管合規需求（如個資法、金管會規定）目前未涉及，面試時若被問到需要補充說明

---
---

# Phase 2：Conversation Design

## ① Requirement & Discovery

**為什麼需要專門的對話設計階段？**
AI 的回答品質不只取決於模型，更取決於對話流程的設計。如果沒有明確定義每個意圖的回應方式、Fallback 策略、Human Handoff 條件，實作時會充滿不確定性。先把對話設計好，程式碼才有明確的目標。

**這個階段要回答的核心問題：**
- 用戶說了什麼 → AI 應該做什麼
- AI 不知道怎麼回答時 → 怎麼處理
- 什麼情況下應該轉真人 → 轉接的門檻是什麼

## ② Design Decision

**Intent Taxonomy 的設計思考：**
初版只有 3 個大類（FAQ / ACCOUNT / WORKFLOW）。設計過程中發現需要再加 ESCALATION（投訴、轉接）和 OUT_OF_SCOPE（範圍外問題），因為這兩種情況在真實使用中會高頻出現，若沒有明確設計，AI 會不知道如何處理。

**Fallback 門檻的選擇：**
設定連續 3 次 Fallback 才觸發 Human Handoff。考慮過 2 次，但覺得太敏感；考慮過 5 次，但用戶體驗太差。3 次是在「給 AI 機會」和「不讓用戶等太久」之間的平衡點。

**對話記憶 10 輪的選擇：**
保留 10 輪（5 問 5 答）是為了平衡上下文理解能力和 token 成本。銀行客服對話通常不超過 5-6 輪就會解決，10 輪提供了足夠的緩衝。

## ③ Implementation & Iteration

*（本階段為文件產出，無實作內容）*

## ④ Evaluation & Reflection

**有效的部分：**
- UC-03 信用卡掛失的 5 步驟流程設計清楚，每個步驟都有明確的輸入、驗證、輸出
- Fallback 策略表格讓「什麼情況記錄、什麼情況不記錄」一目了然
- Mermaid 流程圖在 GitHub 自動渲染，視覺效果比純文字好很多

**下一版需要改善：**
- 中英文混用（Chinglish）的處理邏輯還不夠細緻，需要在實作時測試實際效果
- 對話流程目前只有文字腳本，Phase 8 Portfolio 時考慮錄製實際對話影片

---
---

# Phase 3：Solution Architecture

## ① Requirement & Discovery

**為什麼需要正式的架構設計階段？**
沒有架構圖就開始寫程式，很容易在模組之間的介面上卡住。先定義清楚「誰呼叫誰」「資料怎麼流」「每個元件的職責是什麼」，實作時才有明確的邊界。

**這個階段要回答的核心問題：**
- 系統由哪些元件組成
- 每個 Use Case 的資料流是什麼
- API 長什麼樣子（讓 Swagger 有內容）
- 資料庫存什麼、怎麼存

## ② Design Decision

**最重要的決策：兩層技術策略**
設計文件層（企業標準：Next.js、LangGraph、PostgreSQL、Docker）和實作層（作品集版：Streamlit、函式路由、SQLite）分開。這個決策讓我可以展示完整的企業思維，同時在可控的技術範圍內實際做出來。

**ADR 的引入：**
被問到「你怎麼決定這個技術選型？」時，意識到光有架構圖不夠，需要一份記錄「為什麼這樣選」的文件。ADR 的格式讓每個決策都有：背景、決策、理由、Trade-off、生產環境方案，這五個維度足以回答任何面試追問。

**DB Schema 的設計思考：**
`unresolved_queries` 表記錄了 `trigger_reason`（low_similarity / handoff / api_failure），讓日後分析時可以區分「知識庫缺漏」和「用戶要求轉接」，這兩種情況的優化方向完全不同。

## ③ Implementation & Iteration

*（本階段為文件產出，無實作內容）*

## ④ Evaluation & Reflection

**有效的部分：**
- Mermaid 系統架構圖在 GitHub 上渲染效果好，可以直接展示給面試官
- ADR 7 個條目覆蓋了幾乎所有主要技術選型，面試時有充分的「說故事」素材
- 生產環境升級路徑表格（Section 8）讓面試官看到「這不只是 Demo，有完整的擴展思維」

**下一版需要改善：**
- 架構圖目前只有文字版 Mermaid，Phase 8 考慮用 draw.io 做一張更精緻的視覺版
- API endpoint 的 Request / Response schema 可以在 Phase 6 實作後補充真實的範例

---
---

# Phase 4：Knowledge Base

## ① Requirement & Discovery

**核心問題：沒有真實銀行資料，怎麼辦？**

這是作品集專案最現實的挑戰。真實銀行的 FAQ 文件、CRM 資料都是內部機密，無法取得。最初有兩個選項：
1. 找公開的銀行官網截圖，手動整理
2. 設計合成資料（Synthetic Data），仿照業界標準格式

選擇了合成資料，原因是：公開資料格式零散，且版權不明；合成資料可以完全控制結構和覆蓋範圍，且面試時更容易說明「介面設計為可替換」。

**知識庫需要覆蓋哪些主題？**

根據 Phase 1 的 Intent Taxonomy 設計，FAQ 類別共有 8 個子意圖，因此知識庫也對應設計 8 個主題文件：
- 信用卡費用、信用卡優惠、帳戶服務、轉帳規則、ATM 服務、貸款概覽、數位銀行、一般服務

中英文各一份，合計 16 個 Markdown 文件。

## ② Design Decision

**決定一：每個主題一個文件，而非所有 FAQ 合成一個大文件**

選擇多文件結構，原因：
- RAG 的 Source Attribution（來源顯示）在面試中是加分項。「回答來自 credit_card_fees.md」比「回答來自 faq_all.md」更具說明力
- 維護性好：日後只需修改對應的主題文件，不需翻找大文件
- Chunking 後的 metadata 更清晰（source 欄位有意義）

**決定二：語言路由用獨立 Index，而非單一多語言 Index**

語言路由邏輯：`langdetect` 偵測輸入語言 → 路由到 `zh.index` 或 `en.index`。

原本考慮用單一多語言 FAISS index（`paraphrase-multilingual-mpnet-base-v2` 支援），但最終選擇分開，原因：
- 向量空間中，中英文同義詞的向量距離不一定夠近，可能造成搜尋混淆
- 分開 index 讓中文問題只搜中文文件，英文問題只搜英文文件，結果更可預測
- ADR-07 有詳細說明這個 trade-off

**決定三：Mock 客戶資料設計三個 Persona**

三個 Persona 對應三種使用情境：
- `user_001`（陳小明）：一般上班族，持 2 張信用卡，帳單金額適中
- `user_002`（王大明）：高消費商務人士，持無限卡，帳單金額高
- `user_003`（陳春花）：銀髮族，持基本金卡，有定存帳戶

這樣設計讓 demo 時可以展示不同場景，也能測試 AI 對不同資料結構的理解。

## ③ Implementation & Iteration

**知識庫文件撰寫策略**

採用「結構化 Markdown」格式，而非自然文字段落：
- 表格呈現費用、限額、服務時間（適合 RAG Chunking 後保留關鍵數字）
- 每個主題末尾有 FAQ 問答（模擬用戶真實問法，提高 RAG 匹配率）
- 同時用中文和英文撰寫，確保語言對等性

**Chunking 參數設計（預設 Sprint 5 實作）**

- Chunk Size：400 words（約 600 中文字），避免單一 chunk 太短失去語境、太長增加 noise
- Overlap：80 words，確保跨 chunk 的資訊不遺失（例如表格標題和內容分在不同 chunk）
- 這些參數設計在 `build_index.py` 中有詳細注釋，Sprint 5 驗證後可調整

**`build_index.py` 作為佔位符的意義**

Sprint 1-4 使用 Context Stuffing，不需要真正執行 FAISS。但在 Phase 4 就寫好這個腳本的原因：
- 展示知識庫架構的完整性（不只是文件，還有處理管線設計）
- 幫自己確認 chunking 邏輯是否可行
- Sprint 5 時只需解除注釋（uncomment）即可使用

## ④ Evaluation & Reflection

**成果驗收**

- 中文文件 8 個：`credit_card_fees.md`、`credit_card_benefits.md`、`account_services.md`、`transfer_rules.md`、`atm_services.md`、`loan_overview.md`、`digital_banking.md`、`general_services.md`
- 英文文件 8 個：內容與中文對等
- Mock 客戶資料：3 個 Persona，含帳戶餘額、信用卡資料、帳單、交易明細
- `build_index.py`：Sprint 5 佔位符，已設計好 chunking 邏輯和完整 TODO

**發現的問題**

- 知識庫中的利率、費用數字是虛構的（非真實銀行數字），這是作品集的限制。面試時需要主動說明這一點，並強調「介面設計完全相容於真實文件」。
- 貸款相關文件（`loan_overview.md`）需要特別注意 Disclaimer 觸發設計，確保 AI 不會直接建議用戶申請特定產品。這個邏輯將在 Phase 5 的 Prompt Engineering 中處理。

**下一步（Phase 5）**

Phase 4 完成後，知識庫結構已確定。Phase 5 的重點是設計 AI Agent 的行為：
1. System Prompt：設定銀行 AI 的角色和行為規則
2. Intent Classifier Prompt：如何從用戶輸入判斷意圖
3. Safety Guard：哪些問題不該回答
4. RAG Answer Prompt：如何根據知識庫 context 生成回答
5. Workflow Prompt：掛失流程中每個步驟的對話設計

---
---

# Phase 5：AI Agent Design

## ① Requirement & Discovery

**這個階段要解決什麼問題？**

Phase 1-4 完成了「做什麼」（PRD、Conversation Design、Architecture、Knowledge Base），Phase 5 要定義「怎麼做」——AI 的行為規格。

在 Phase 4 結束後，知識庫已建立，但 AI 還不知道：
- 如何判斷用戶想要什麼（意圖分類）
- 判斷出意圖後，要怎麼回答（RAG / API / Workflow）
- 什麼情況下不該回答（Safety Guard）
- 掛失流程的每個步驟說什麼

這些設計如果不事先寫清楚，實作時就會每個問題都需要「現場決定」，品質不一致。

**這個階段的核心輸出：**
把 Phase 1-3 的需求，翻譯成 AI 可以執行的 Prompt 規格，讓 Sprint 實作時有明確依據。

## ② Design Decision

**決定一：Intent Classifier 獨立於主對話**

意圖分類使用獨立的 LLM 呼叫，輸出結構化 JSON，而非讓主對話 AI 在回答中「暗示」意圖。

理由：
- 分類結果機器可解析，不依賴文字解讀
- 可單獨測試分類準確率（建立 30 個測試案例，目標 > 90%）
- 未來可替換為更快的小模型，不影響主對話品質

**決定二：Safety Guard 分三層，最高優先級硬編碼**

非財務問題：Intent-level 攔截（不送 LLM，直接返回拒絕訊息）
財務 Disclaimer：程式碼層強制插入（不依賴 AI 自行判斷何時加）
詐騙情境警告：完全繞過 LLM，返回硬編碼的標準化警告

這個設計的面試說法：「最高風險的邊界由程式碼控制，而非 AI 判斷」。

**決定三：Workflow Prompt 按步驟分離，而非一個大 Prompt**

信用卡掛失的 5 個步驟，每個步驟用不同的 Prompt，原因：
- 每步驟的 context 不同（Step 1 需要 id_last4、Step 2 需要 cards list）
- 每步驟的失敗處理不同（Step 1 最多 3 次、Step 3 可取消）
- 一個大 Prompt 包含所有步驟會讓 AI 混淆當前在哪個步驟

**決定四：RAG Answer Prompt 強調 Context-only**

RAG Prompt 的核心約束是「只根據提供的 Context 回答，不使用訓練知識補充」。
這個限制讓幻覺的空間縮小到「改寫知識庫內容」的範圍，比「憑空生成」風險低得多。

## ③ Implementation & Iteration

**產出物清單：**

| 文件 | 內容 |
|------|------|
| `docs/agent_design.md` | AgentState TypedDict、6 個 Node 設計、9 個 Tool spec、LangGraph 流程圖 |
| `docs/prompt_engineering/system_prompt.md` | System Prompt v1.0 + 版本歷史 + 測試案例 |
| `docs/prompt_engineering/intent_classifier.md` | 分類 Prompt + 路由邏輯 + 10 個測試案例 |
| `docs/prompt_engineering/safety_guard.md` | 三層安全設計 + 詐騙偵測 + Disclaimer 注入邏輯 |
| `docs/prompt_engineering/rag_answer.md` | Context-only Prompt + Sprint 1-4 Stuffing 版 + Sprint 5 RAG 版 |
| `docs/prompt_engineering/workflow_card_loss.md` | 5 步驟完整 Prompt + 邊界情境表格 |

**設計過程中發現的問題：**

- `workflow_data` 需要在 AgentState 中設計為 mutable dict，允許逐步填入（id_last4、card_id、ticket_id），這個結構在 Sprint 3 實作時需要小心初始化
- Intent Classifier 的 `unclear` 情境需要一個「最多問 2 次再提供選單」的機制，這個計數器也需要在 AgentState 中追蹤

## ④ Evaluation & Reflection

**有效的部分：**
- Prompt 規格文件讓每個 Sprint 的實作有明確依據，不需要在寫程式時臨時決定 AI 說什麼
- 9 個 Tool spec 用 OpenAI-compatible 格式撰寫，Sprint 6 移植到 LangGraph 時可直接使用
- Safety Guard 的三層架構清楚說明了責任分界，面試時可以系統性地回答「如何防止 AI 幻覺」

**下一步（Sprint 0 → Sprint 1）：**
Phase 5 文件完成後，正式進入實作階段。

Sprint 0（專案骨架）：
- 建立 `requirements.txt`
- 建立 `backend/main.py` FastAPI 骨架
- 建立 `frontend/app.py` Streamlit 骨架
- 確認 `.env` 和 `ANTHROPIC_API_KEY` 設定

Sprint 1（FAQ with Context Stuffing）：
- Streamlit 聊天介面 + FastAPI `/chat` endpoint
- 使用 Context Stuffing + System Prompt 回答 FAQ
- 通過 10 個基本 FAQ 測試問題

---
---

# Sprint 1：FAQ（Context Stuffing）

## ① Requirement & Discovery

*(Sprint 1 開始後填寫)*

## ② Design Decision

*(Sprint 1 開始後填寫)*

## ③ Implementation & Iteration

*(Sprint 1 完成後填寫)*

## ④ Evaluation & Reflection

*(Sprint 1 完成後填寫)*

---
---

# Sprint 6：LangGraph 重構

## ① Requirement & Discovery

Sprint 1-5 已經把 FAQ、帳務查詢、信用卡掛失、真人轉接、未解決記錄五種行為，全部用 `backend/main.py` 裡一連串 `if/else` 撐起來。邏輯是對的，但 `/chat` 這個函式一路長到 371 行，五種分支的輸入輸出混在一起，沒有任何一個地方能單獨看到「這個意圖進來、產生了什麼 state」。ADR-002 早就寫好了要在這個時間點升級：先讓業務邏輯跑通、驗證過，再換架構。Sprint 6 就是兌現這個承諾——目標不是新增功能，是把已經驗證過的行為，重新組織成有明確邊界、可追蹤 State 的 Graph。

## ② Design Decision

**維持「外部行為完全一致」的硬限制**：`docs/agent_design.md` 開頭就寫「Sprint 1-5 與 Sprint 6 的外部行為一致，差異只在內部架構」，所以重構過程中不新增、不修改任何使用者可觀察到的行為，純粹是把同一段邏輯搬進 Router / CardLoss / Handoff / FAQ / Account / Logger 六個 Node。

**FAQ Node 和 Account Node 共用同一個實作**：這是最大的取捨。`docs/agent_design.md` §3.2/§3.3 把 FAQ 和 Account 寫成兩個獨立 Node，但 Sprint 1-5 的實際行為是——不管使用者問的是知識庫問題還是帳務問題，都丟進同一次 Claude 呼叫，system prompt 裡同時塞 RAG chunks 和使用者帳務資料（`format_user_context`）。如果為了呼應設計文件硬拆成兩個真正獨立的 LLM 呼叫，等於改變了實際行為（例如「我的信用卡年費是多少，另外我這個月帳單多少」這種混合問題，原本一次回答，拆開後可能要問兩次）。所以最後選擇：Router 仍然分類並標記 `intent="faq"` 或 `"account"`（State 上看得到、log 也分得開），但兩者路由到同一個 `qa_node`。這個決定的理由要在面試時說清楚：Node 邊界是為了可觀察性和未來擴充（如果之後真的要幫 Account 接 `get_account_balance` 之類的 tool call，只需要新增一個真正獨立的 Account Node，不影響 FAQ），不是為了現在就過度設計。

**Logger Node 要撐住「一輪可能觸發兩次 log」的既有行為**：原本的 `if/else` 裡，`negative_feedback` 檢查和 RAG `low_similarity` 檢查是兩段獨立的程式碼，同一則訊息如果兩個條件都成立，會呼叫兩次 `log_unresolved`。重構時一開始想把 Logger 簡化成「只記一筆」，後來意識到這樣會悄悄改變外部行為（DB 記錄筆數變少），違反①的硬限制。最後讓 State 帶一個 `log_entries: list[dict]`，`qa_node`/`handoff_node` 各自往裡面 append，`logger_node` 迴圈寫入——這樣兩次 log 的行為原封不動保留。

## ③ Implementation & Iteration

把原本塞在 `main.py` 裡的關鍵字判斷（`is_card_loss`／`is_handoff_trigger`／`is_negative_feedback`）和語言偵測搬到新的 `backend/src/nlp.py`；system prompt 組裝（`build_system_prompt`／`format_user_context`／`CONFIGS`）搬到 `backend/src/prompts.py`。新增 `backend/src/agent/`（`state.py` 定義 `AgentState`、`nodes.py` 六個 Node 函式、`graph.py` 用 `langgraph.graph.StateGraph` 接線）。`main.py` 的 `/chat` endpoint 縮到只剩：組出 initial state → `agent_graph.invoke()` → 轉成 `ChatResponse`，Pydantic 的 `ChatRequest`／`ChatResponse` 完全沒動，前端 Streamlit 不用改一行。

驗證方式：先用假的 `client`／`retriever`（回傳固定字串，不打真的 API）跑過六條路徑確認 Graph 走線正確；接著啟動真正的 `uvicorn`，用實際的 Claude API + FAISS index 跑了 FAQ（中英各一）、已登入帳務查詢、完整四步驟信用卡掛失流程、關鍵字轉真人、負面回饋+低相似度同時觸發五種情境，逐一比對 `/tickets`、`/unresolved`、`/stats` 三個 dashboard endpoint 的寫入結果，確認和 Sprint 5 的行為（包含「一輪兩筆 log」這個邊角案例）完全一致。

## ④ Evaluation & Reflection

實測跑下來，六個 Node 的行為和重構前逐項核對都一致，包含最容易漏掉的邊角案例：使用者在掛失流程中途被登出（`workflow_step > 0` 但沒有 `user_id`）時，原本的程式碼會把 workflow 悄悄重置成 step 0——這其實比較像是 Sprint 1-4 沒注意到的行為，而不是刻意設計。重構時選擇原封不動保留這個行為（沒有藉機「順手修掉」），因為 Sprint 6 的任務是重構架構、不是修正邏輯，兩件事分開做才不會讓「行為有沒有變」這個驗證變得混亂。這個小案例本身也是面試時可以講的故事：重構最大的風險不是寫錯新程式碼，而是「順手」把舊的（不管是不是 bug）行為改掉。

下一版如果要繼續往前，Account Node 是最明確的候選：接上 §4 定義的 `get_account_balance`／`get_credit_card_bill`／`get_transactions` 等 tool spec，讓 Account 查詢真正走結構化 API 呼叫而不是整包 context stuffing，這樣可以顯著縮小 system prompt、也更貼近企業產線常見的 tool-calling Agent 設計。

---
---

# Sprint 7：Account Node Tool-Calling

## ① Requirement & Discovery

Sprint 6 的反思裡已經寫得很清楚：Account Node 只是 Router 貼的一個標籤，實際查帳務問題還是走 FAQ Node 那套 context stuffing——把整個使用者的存款、信用卡、帳單、近期交易全部塞進 system prompt，不管使用者只是問「餘額多少」。這在作品集面試時是個明顯的破綻：一個宣稱懂 Agent 架構的人，Account「Node」卻沒有真正做到「Node」該做的事。Sprint 7 的目標很單純：把這筆 Sprint 6 刻意欠下的技術債還掉，讓 Account Node 變成一個真正會呼叫 tool 的 Agent。

## ② Design Decision

**Account 從此和 FAQ 分家，各自獨立呼叫 Claude**：不再共用 `qa_node`。Account Node 有自己的 system prompt（只講帳務規則、不帶 RAG）、自己的 tools 參數、自己的 tool-use 迴圈。這是 Sprint 6 沒做但已經預告的事——現在條件成熟了（Sprint 6 已經把 Node 邊界搭好），可以放心拆。

**`user_id` 不給模型填，後端注入**：這是這次最重要的安全決策。`docs/agent_design.md` §4.2-4.4 原始的 tool spec 把 `user_id` 列成參數之一，是為了描述一個「通用」的工具介面；但如果照抄進 Claude 看得到的 schema，等於讓模型自己決定要查誰的帳戶——萬一被 prompt injection（例如使用者在對話中說「幫我查 user_003 的餘額」）操控，就有跨用戶查詢的風險。所以 `backend/src/agent/tools.py` 的 `ACCOUNT_TOOLS` 故意不包含 `user_id`，改由 `execute_tool()` 在執行當下從已驗證的 session state 注入。這個決定值得記下來，因為它是「照抄設計文件 vs. 自己多想一步」的具體案例。

**FAQ Node 的 context stuffing 保留當安全網**：Router 用關鍵字判斷 `is_account_query`，一定會有誤判（例如「信用卡年費」被誤判成 FAQ，或反過來）。與其花時間把關鍵字規則調到完美，選擇讓 FAQ Node 的 system prompt 繼續帶著使用者帳務資料——就算 Router 判斷錯，使用者也不會得到「查不到」的爛體驗，只是沒有用到 tool-calling 的精準度。這是刻意保留的重複，不是漏掉沒清理。

## ③ Implementation & Iteration

在 `backend/src/mock_api/mock_data.py` 新增三個純函式（`get_account_balance`／`get_credit_card_bill`／`get_transactions`），對應 §4.2-4.4 的資料形狀。新建 `backend/src/agent/tools.py` 定義 Anthropic tool schema 和 `execute_tool()` dispatcher。`nodes.py` 新增 `make_account_node()`：先檢查 `user_id`，未登入直接回登入提示（不打 API）；已登入則跑 tool-use 迴圈（最多 `MAX_TOOL_ITERATIONS=3` 輪，防止模型卡在無限呼叫工具）。`graph.py` 把 `account` 意圖從 `qa` 節點改指到新的 `account` 節點。

驗證方式：實測餘額查詢、帳單查詢、交易明細查詢、以及一次問兩件事（「活期餘額多少，最近花了什麼」）確認模型會依序呼叫兩個工具再整合回答；也測了未登入時查帳務資訊，確認完全不觸發 Claude 呼叫、直接回登入提示。同時跑了 FAQ 和信用卡掛失流程的回歸測試，確認沒有被這次改動波及。

## ④ Evaluation & Reflection

混合問題（一次問餘額又問交易）那個測試案例特別能說明 tool-calling 相對 context stuffing 的優勢：Claude 自己決定要呼叫兩個工具、依序取得資料再整合成一段自然語言回答，而不是像之前那樣不管問什麼都把所有資料倒給它讀。輸出品質沒有變差，但 system prompt 大小和資料曝露範圍都明顯縮小。

比較意外的收穫是「`user_id` 由後端注入」這個決定——一開始只是照著 §4 的 tool spec 抄，抄到一半才意識到「如果 Claude 自己填 user_id，這個工具就是不安全的」。這提醒了自己：設計文件是 Sprint 6 之前寫的規格，寫規格的時候還沒有認真想過 prompt injection 這個角度，執行到這一步才補上，說明「先寫文件、再寫程式」的流程本身不能取代寫程式當下的安全意識。

下一版如果要繼續往前，比較明確的候選是把 Router 的關鍵字分類（`is_account_query` 等）換成真正的 LLM Intent Classification，減少誤判；另一個方向是幫 CardLoss Workflow 也導入 tool-calling（`verify_identity`／`block_card`／`create_ticket` 目前都是直接呼叫 Python 函式，沒有經過 Claude 決策），但這個改動風險較高，需要先想清楚多步驟工作流程和 tool-calling 迴圈要怎麼共存。

---
---

# Sprint 8：測試套件

## ① Requirement & Discovery

Sprint 1-7 每一輪都是手動測試——啟動 `uvicorn`、用 curl 或 Python script 打幾個請求、看結果對不對、然後關掉 server，測試腳本沒有留下來。這樣做的問題在 Sprint 6/7 交界處就露出來了：兩次都要重新手動驗證同一批舊行為（FAQ、Handoff、CardLoss）沒有被新改動波及，而且有一次手動測試甚至把真的 `banking.db`（面試展示用的 Dashboard 資料）弄髒了，得手動清資料列。這次的目標是把「驗證系統沒壞」這件事，從一次性的手動動作變成可以留在 repo 裡、隨時重跑的東西。

## ② Design Decision

**測試用資料庫要完全獨立，不跟真實 demo 資料共用檔案**：討論了兩個方案——(A) 獨立 `test.db`、(B) 每次測試後自動清除新增的資料列。方案 B 的風險是：如果測試中途 assert 失敗或程式當掉，清除邏輯根本不會執行，垃圾資料就留在真實 `banking.db` 裡（這正是這次 Sprint 6/7 之間手動測試時實際發生過的事）。方案 A 結構上更安全——就算測試寫錯、當掉，最壞情況也只是 `test.db` 裡有垃圾，重新產生一次就好，不會動到用來展示的 Dashboard 資料。代價是要把 `backend/src/database.py` 原本寫死的 `DB_PATH` 改成可以用環境變數 `BANKING_DB_PATH` 覆寫，`tests/conftest.py` 在 import `backend.main` 之前先設好這個環境變數。

**測試斷言只驗證「結構」，不驗證「LLM 說了什麼」**：FAQ 和 Account Node 每次呼叫 Claude，用字遣詞都會變，沒辦法寫 `assert response == "..."`。這次的分工很明確：pytest 只負責驗證確定性的部分——語言偵測對不對、意圖有沒有路由到對的 Node、workflow_step 有沒有正確推進、tool 有沒有被呼叫、DB 有沒有寫入正確的 ticket/log；回答「寫得好不好」留給人工，checklist 已經整理在跟使用者的討論記錄裡（語言正確性、有沒有幻覺、disclaimer 出現時機、中英文語意對齊等）。這個分工意外地讓一大部分測試變得完全免費——CardLoss 和 Handoff 兩個 Node 本來就是純 Python 邏輯，完全不呼叫 Claude，所以這兩個檔案的測試是零 token 成本，也因為沒有 LLM 的不確定性，可以放心用 `assert ... ==` 精確比對。真正會呼叫 API、需要保持斷言寬鬆的，只有 FAQ 和 Account 兩個檔案。

**測試資料用不同的 mock user 隔開，而不是靠 fixture reset**：`MOCK_USERS` 是 Python 記憶體裡的全域字典，`block_card()` 會直接改掉裡面卡片的狀態。因為每次執行 `pytest` 都是全新的 Python process，`MOCK_USERS` 本來就會重新從原始碼載入，不需要額外寫 reset 邏輯；只要確保「會改變卡片狀態」的測試（掛失流程走到底）跟其他測試用不同的 demo 帳號（`user_002` 專門給完整掛失流程用，`user_001` 只做唯讀的帳務查詢，`user_003` 給中途取消的流程用），彼此就不會互相干擾。

## ③ Implementation & Iteration

新增 `tests/conftest.py`：在 import `backend.main` 之前設定 `BANKING_DB_PATH` 指向 `tests/test.db`，用 session-scoped 的 `TestClient` fixture（`with TestClient(app) as c`）觸發一次真正的 FastAPI startup event（`init_db()`、RAG retriever 載入、LangGraph build），整個測試 session 只需要載入一次 embedding model，而不是每個測試都重新載入一次。新增 `pytest.ini` 設定 `pythonpath = .`，確保不管用 `pytest` 還是 `python -m pytest` 執行，`backend.*` 的 import 都能正確解析。

四個測試檔案：`test_faq.py`（FAQ 中英文、負面回饋+低相似度雙重 log 的回歸測試）、`test_account.py`（未登入拒答、餘額/帳單/交易查詢、混合問題觸發多個 tool）、`test_card_loss.py`（完整四步驟流程並驗證 ticket 正確建立、中途取消、未登入、身分驗證失敗重試）、`test_handoff.py`（關鍵字觸發、`force_handoff` flag）。總共 14 個測試案例，跑一輪大約 40 秒。

驗證方式：連續跑兩次確認結果一致（沒有測試間互相汙染）；跑完後直接檢查真實 `data/banking.db`，確認 ticket 數量和 unresolved_queries 筆數完全沒有變化，證明隔離確實有效；也確認沒設 `BANKING_DB_PATH` 時 `DB_PATH` 仍正確預設回原本的路徑，production 行為不受影響。

## ④ Evaluation & Reflection

意外的收穫是 CardLoss 和 Handoff 兩個 Node 的測試完全零成本——一開始以為「整套測試套件」意味著全部都要打 Claude API、要精算 token 預算，實際動手才發現真正呼叫 LLM 的只有 FAQ 和 Account 兩塊，其餘的路由、狀態機、DB 寫入邏輯都是確定性的 Python，可以又快又精準地測。這也間接印證了 Sprint 6 的 Node 化設計是對的方向：邊界清楚之後，才看得出哪些部分是「AI 決策」、哪些部分是「工程邏輯」，兩者需要完全不同的測試策略。

`negative_feedback_and_low_similarity_dual_log` 這個測試特別值得一提：它不是新寫的功能測試，而是把 Sprint 6 design journal 裡提到的「一輪對話可能觸發兩筆 log」這個容易被未來的自己不小心「順手修掉」的邊角行為，轉成一個會在 CI 或下次改動時自動失敗的斷言。這是測試套件相對於手動測試最大的價值——手動測試驗證的是「現在對不對」，自動化測試保護的是「以後會不會被悄悄改壞」。

下一步如果要讓這套測試更完整，比較明確的候選是：(1) 把 `on_event("startup")` 換成 FastAPI 建議的 `lifespan` 寫法，消除目前測試輸出裡的 deprecation warning；(2) 若之後想接 GitHub Actions 秀 CI 徽章，需要另外決定 `ANTHROPIC_API_KEY` 怎麼安全地存進 GitHub Secrets，以及能不能接受每次 push 都燒一次 token 的成本。

---
---

# Sprint 9：Router LLM Intent Classification

## ① Requirement & Discovery

`docs/agent_design.md` §3.1 從專案一開始（Phase 5，寫在 Sprint 1 之前）就把 Router 定義成「Intent Classification（LLM 分類）」，但 Sprint 1-8 一直是用關鍵字比對頂著——這件事在 Sprint 7、Sprint 8 的反思裡都各自提過一次，是明確欠著的一筆債。這次要還的不是新功能，是讓實作終於對齊最早寫下的設計文件。動機也很具體：關鍵字比對的失敗模式是結構性的，不是清單不夠長的問題——它只能比對「有沒有出現特定字」，沒辦法理解語意，遇到清單沒覆蓋到的講法就會誤判。

## ② Design Decision

**用 `tool_choice` 強制結構化輸出，不解析自由文字**：分類器呼叫 Claude 時用 `tool_choice={"type": "tool", "name": "classify_intent"}` 強迫模型一定要呼叫這個 tool、一定要從四個分類（`faq`／`account`／`card_loss`／`handoff`）裡選一個。這樣拿到的結果保證合法，不需要處理「模型沒照格式回答」這種例外，也不用寫文字比對或 regex 去猜模型想表達哪個分類。這個做法直接複用了 Sprint 7 已經驗證過的 tool-calling 模式，只是這次工具不是拿去查資料，而是拿來逼出一個結構化分類結果——算是同一個技術手法的第二種用法，這點在面試時值得提。

**兩種情況刻意不呼叫分類器**：掛失流程進行中（`workflow_step > 0`）和前端強制轉真人（`force_handoff`，連續 fallback 達門檻）維持原本的確定性判斷，直接跳過 LLM。這兩者本質上是「系統目前處於什麼狀態」，不是「使用者這句話是什麼意圖」——如果連這個都交給 LLM 判斷，等於把一個原本 100% 確定的邏輯，換成一個有機率誤判的邏輯，沒有任何好處，純粹增加延遲和不確定性。這個判斷跟 Sprint 6 保留「一輪兩筆 log」行為是同一種思路：分清楚「這是系統狀態」還是「這是需要理解的內容」，兩者的處理方式不該混在一起。

**FAQ Node 的 context stuffing 繼續留著當安全網**：這個決定 Sprint 7 就做過一次，這次沒有理由推翻——即使分類器比關鍵字準，還是有機率誤判，FAQ Node 的 system prompt 仍然帶著使用者帳務資料，誤判時不會完全答不出來。

## ③ Implementation & Iteration

新增 `backend/src/agent/intent.py`：`INTENT_CLASSIFIER_TOOL` 定義四分類 tool schema，`classify_intent()` 用強制 tool_choice 呼叫並取出分類結果。`nodes.py` 的 `router_node` 改寫成 `make_router_node(client, model)` 工廠函式，保留 `workflow_step > 0` 和 `force_handoff` 兩個確定性分支，其餘交給 `classify_intent()`。`nlp.py` 刪掉三個變成死代碼的關鍵字函式（`is_card_loss`／`is_handoff_trigger`／`is_account_query`）和對應的關鍵字清單，只留 `is_negative_feedback`（FAQ/Account Node 內部用，跟路由是不同關注點）和 `detect_language`。

第一版寫完直接被 Sprint 8 的測試套件抓到一個問題：`test_negative_feedback_and_low_similarity_dual_log`（Sprint 6 就存在的回歸測試）失敗，原因是「你搞錯了，這不是我要的答案」被分類器誤判成 `handoff`——這句話單獨看確實像在抱怨，分類器沒有上下文，判斷「使用者聽起來不爽 = 想找真人」不是完全沒道理的推論，但這跟系統原本的設計不符（單純的負面回饋走 `negative_feedback` log，不直接升級成 Handoff）。修法是在 tool description 裡明確列出反例（「單純說答案不對／沒幫助，不算要求轉真人」），並補一個 `no prior conversation` 的提醒，讓模型知道自己只看得到這一句話、沒有前後文可以判斷。修完後另外寫了 `tests/test_router_intent.py` 直接測 `classify_intent()` 本身（不透過完整 `/chat`），把這個案例釘成一個獨立的分類器回歸測試——這樣以後如果又不小心把 tool description 改壞，能直接定位到是分類器的問題，不用先猜是不是 FAQ Node 或 DB 寫入壞了。

順手處理了兩個因為改名而出現的殘留：`trigger_reason` 從 `"handoff_keyword"` 改名成 `"handoff_intent"`（因為觸發方式已經不是關鍵字了），這個字串同時出現在 `nodes.py` 的預設值和 `frontend/pages/1_Dashboard.py` 的兩個 Dashboard 圖表 label 對照表裡——後者如果沒改，Dashboard 上「要求真人」這個分類會因為字典查不到 key 而直接顯示英文原始字串，不會報錯但會很難看，算是那種「不會壞、但會露餡」的細節。

驗證方式：連續跑兩次完整 pytest 套件（19 個測試，含新增的 `test_router_intent.py` 5 個案例）確認結果穩定；跑完後檢查真實 `data/banking.db` 沒有任何變化，確認 Sprint 8 的隔離設計在這次改動後依然有效。

## ④ Evaluation & Reflection

這次最有價值的部分不是分類器本身寫出來了，而是「寫完馬上被自動化測試抓到一個沒預料到的誤判案例」這個過程本身——如果沒有 Sprint 8 先把測試套件建起來，這個誤判很可能要等到手動測試、甚至demo 時才會被發現，而且很可能被忽略過去（畢竟「你搞錯了」被當成抱怨要轉真人，語意上不算離譜，不仔細看行為對不對就很容易滑過去）。這也是這幾個 Sprint 疊起來的複利效果：Sprint 6 定義清楚 Node 邊界、Sprint 7 建立 tool-calling 模式、Sprint 8 把回歸測試變成可重跑的東西，Sprint 9 才有辦法在改動當下就抓到問題，而不是憑感覺相信「LLM 應該分得出來」。

比較意外的收穫是「Sprint 9 讓測試套件的成本模型也跟著變了」——Sprint 8 完成時特別強調 CardLoss／Handoff 測試零成本，因為關鍵字路由不呼叫 API；Sprint 9 把路由本身換成 LLM 之後，這個「零成本」的說法已經不完全準確（每個流程的第一句觸發訊息現在都要過一次分類器）。這提醒了自己：文件裡寫「零成本」這種具體宣稱時，要意識到它是建立在當下架構上的，架構一變就要回頭檢查有沒有跟著過時——這次有記得回去更新 Sprint 8 測試檔案的 docstring，但如果沒有測試套件這個明確的參照物，這種文件跟實作脫節的狀況很容易被忽略。

下一步如果要讓 Router 更完整，比較明確的候選是 §3.1 提到但 v1 一直沒做的「意圖分類信心度低 → 反問用戶」——現在用 `tool_choice` 強制輸出，拿到的是確定結果，沒有信心分數可以判斷模型是不是在瞎猜，如果要做需要換一種呼叫方式（例如比較拿掉強制呼叫後模型會不會遲疑、或用 logprobs）。這個功能對「展示核心 Agent 架構」的邊際效益不高，暫不列入下一個 Sprint。

---

*後續 Sprint 依此格式持續新增*
