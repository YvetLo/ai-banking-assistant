# Prompt Engineering Portfolio
# AI Banking Customer Assistant

這個資料夾記錄本專案所有 Prompt 的設計過程、版本迭代與測試結果，
作為 Prompt Engineering 能力的具體展示。

---

## 為什麼 Prompt Engineering 很重要？

LLM 的行為由 Prompt 決定。好的 Prompt 設計能：
- 讓 AI 只回答知識庫內的資訊，防止幻覺
- 控制語氣、語言、回覆格式
- 定義清楚的邊界（什麼能答、什麼不能答）
- 在不同情境自動切換行為（FAQ / 帳務查詢 / 掛失流程）

---

## Prompt 清單（Phase 5 開始填入）

| 檔案 | 用途 | 設計重點 |
|------|------|---------|
| `system_prompt.md` | 主系統 Prompt | 角色定義、核心規則、語言控制 |
| `intent_classifier.md` | 意圖分類 Prompt | 結構化輸出、分類邊界定義 |
| `safety_guard.md` | 安全防護 Prompt | 拒絕非銀行問題的措辭設計 |
| `rag_answer.md` | RAG 回答生成 Prompt | 忠實於 context、附來源、免責聲明 |
| `workflow_card_loss.md` | 信用卡掛失 Prompt | 步驟引導、確認機制、同理語氣 |

---

## 每份文件的格式

每個 Prompt 文件包含：
1. **Purpose** — 這個 Prompt 解決什麼問題
2. **Design Decisions** — 為什麼這樣設計，考慮過哪些替代方案
3. **Prompt 內容**（版本歷史）
4. **測試案例** — 輸入 / 預期輸出 / 實際輸出
5. **已知限制** — 這個 Prompt 在哪些情況下效果不佳
6. **下一版改善方向**

---

*Phase 5（Agent Design）開始填入具體 Prompt 內容*
