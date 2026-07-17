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

*後續 Sprint 依此格式持續新增*
