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

*後續 Sprint 依此格式持續新增*
