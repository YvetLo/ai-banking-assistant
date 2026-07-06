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

*(填寫中...)*

## ② Design Decision

*(填寫中...)*

## ③ Implementation & Iteration

*(填寫中...)*

## ④ Evaluation & Reflection

*(填寫中...)*

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
