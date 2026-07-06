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

*最後更新：2026-07-06*
*每個 Sprint 遇到新的重要決策時，在此文件新增 ADR 條目。*
