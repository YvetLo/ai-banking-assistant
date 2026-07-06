# Conversation Design Document
# AI Banking Customer Assistant

| 欄位 | 內容 |
|------|------|
| **文件版本** | v1.0 |
| **建立日期** | 2026-07-06 |
| **依據文件** | PRD v1.0 |

---

## 1. 設計原則

| 原則 | 說明 |
|------|------|
| **誠實優先** | 知識庫無答案時，誠實告知，不猜測 |
| **一步一步** | 複雜流程（掛失）拆成清楚步驟，每步確認後再繼續 |
| **語言一致** | 用戶用中文問就中文回，用英文問就英文回 |
| **主動引導** | 用戶問題模糊時，反問釐清，而不是亂猜 |
| **同理心** | 緊急情況（掛失、投訴）語氣更積極、更快速 |
| **責任邊界** | 涉及財務數字一律附加免責聲明 |

---

## 2. Intent Taxonomy（意圖分類）

```
AI Banking Assistant — Intent 完整分類
│
├── FAQ（一般查詢，不需登入）
│   ├── credit_card_fee        信用卡年費、手續費、利率
│   ├── credit_card_benefit    信用卡優惠、回饋、累點
│   ├── account_rule           開戶條件、存款規則、利率
│   ├── transfer_rule          轉帳、匯款、手續費說明
│   ├── atm_service            ATM 提款上限、跨行費用
│   ├── loan_info              房貸、個貸、利率試算說明
│   ├── digital_service        網路銀行、忘記密碼、APP 功能
│   └── general_service        營業時間、分行查詢、客服電話
│
├── ACCOUNT（帳務查詢，需登入）
│   ├── check_bill             查信用卡帳單應繳金額
│   ├── check_balance          查存款餘額
│   └── check_transactions     查交易明細
│
├── WORKFLOW（流程操作，需登入）
│   ├── report_card_loss       信用卡掛失
│   ├── apply_product          產品申辦諮詢引導
│   └── dispute_transaction    爭議款項申請引導
│
├── ESCALATION（轉接）
│   ├── request_human          明確要求真人客服
│   └── complaint              投訴、不滿
│
└── OUT_OF_SCOPE（範圍外）
    ├── off_topic              非銀行相關問題
    └── sensitive              涉及個人隱私、法律、醫療等敏感話題
```

---

## 3. 對話流程設計

### 3.1 開場白

**中文版**：
```
您好！我是 XX 銀行 AI 客服助理 🏦

我可以協助您：
• 查詢信用卡費用、帳單、優惠
• 查詢帳戶餘額與交易明細（需登入）
• 信用卡掛失申請
• 銀行業務一般問題

請問有什麼可以為您服務的嗎？

────────────────────────
⚠️ 本助理提供之資訊僅供參考，不構成財務建議。
   實際利率、費用以官網公告為準。
```

**英文版**（偵測到英文輸入時使用）：
```
Hello! I'm XX Bank's AI Customer Service Assistant 🏦

I can help you with:
• Credit card fees, bills, and rewards
• Account balance and transaction history (login required)
• Credit card loss reporting
• General banking inquiries

How can I assist you today?

────────────────────────
⚠️ Information provided is for reference only and does not
   constitute financial advice.
```

---

### 3.2 UC-01：FAQ 查詢（RAG Mode）

**正常流程（Happy Path）**：

```
[用戶] 信用卡年費多少？

[意圖分類] → FAQ / credit_card_fee
[語言偵測] → 中文
[RAG 搜尋] → knowledge_base/zh/credit_card_fees.md
              Similarity score: 0.87 ✅

[AI 回覆]
信用卡年費依卡別不同，以下是主要卡種說明：

💳 一般卡：年費 $800
   • 每年消費滿 3 筆可申請免年費

💳 白金卡：年費 $3,500
   • 首年免年費
   • 每年消費滿 $150,000 可享永久免年費

💳 無限卡：年費 $18,000
   • 首年免年費（需達核卡標準）

如需申請免年費，可撥打卡背客服電話或至網路銀行辦理。

📄 來源：信用卡費用說明文件
⚠️ 實際年費以您的信用卡合約為準，詳情請參閱官網。

還有其他問題嗎？
```

**英文查詢範例**：

```
[用戶] What is the annual fee for a platinum credit card?

[意圖分類] → FAQ / credit_card_fee
[語言偵測] → English
[RAG 搜尋] → knowledge_base/en/credit_card_fees.md

[AI 回覆]
The annual fee for a Platinum Credit Card is NT$3,500.

Here are the fee exemption conditions:
• First year: Annual fee waived automatically
• Ongoing: Annual fee waived if annual spending exceeds NT$150,000

To apply for an annual fee waiver, please call the service number
on the back of your card or log in to Online Banking.

📄 Source: Credit Card Fee Guidelines
⚠️ Actual fees are subject to your cardholder agreement.

Is there anything else I can help you with?
```

**知識庫無答案（Fallback）**：

```
[用戶] 你們有沒有加密貨幣投資服務？

[RAG 搜尋] → Similarity score: 0.21 ❌ 低於門檻 0.7
[記錄] → unresolved_queries DB

[AI 回覆]
抱歉，關於加密貨幣投資服務，目前我的資料庫中沒有相關資訊。

建議您：
• 撥打客服電話 0800-XXX-XXX 詢問
• 前往最近的分行洽詢理財專員

還有其他我可以幫助您的問題嗎？
```

**非銀行問題（Safety Guard）**：

```
[用戶] 今天台北天氣如何？

[意圖分類] → OUT_OF_SCOPE / off_topic

[AI 回覆]
抱歉，我是 XX 銀行的專屬客服助理，只能協助銀行相關的問題。

如果您有銀行業務需要諮詢，我很樂意幫忙！
例如：信用卡費用查詢、帳單問題、掛失申請等。

請問有銀行相關的問題嗎？
```

---

### 3.3 UC-02：帳務查詢（API Mode）

**已登入正常流程**：

```
[用戶] 我本月信用卡要繳多少？

[意圖分類] → ACCOUNT / check_bill
[Auth Check] → 已登入（user_001）✅
[API 呼叫] → GET /accounts/bill?user_id=user_001&month=2026-07
[Mock API 回傳] → { due_amount: 12450, due_date: "2026-07-25",
                    min_payment: 3500 }

[AI 回覆]
您本月（7 月）信用卡帳單資訊如下：

💰 應繳金額：NT$12,450
📅 繳款截止日：2026 年 7 月 25 日
⚡ 最低應繳金額：NT$3,500

建議在截止日前完成繳款，以避免循環利息。

💡 您可以透過網路銀行、ATM 或便利商店繳款。

需要查詢本月消費明細嗎？
```

**未登入時**：

```
[用戶] 我本月信用卡要繳多少？

[意圖分類] → ACCOUNT / check_bill
[Auth Check] → 未登入 ❌

[AI 回覆]
查詢個人帳單資訊需要先登入您的帳號。

請點選右上角「登入」按鈕，完成驗證後即可查詢。

如果您忘記密碼，可以：
• 使用「忘記密碼」功能重設
• 撥打客服電話 0800-XXX-XXX

完成登入後，我可以立即為您查詢帳單。
```

**多輪對話理解（上下文記憶）**：

```
[用戶] 我本月信用卡要繳多少？
[AI] 您本月應繳金額：NT$12,450，截止日 7/25。

[用戶] 那上個月呢？         ← AI 理解「上個月」= 上個月帳單
[AI 呼叫] → GET /accounts/bill?month=2026-06
[AI 回覆] 您上個月（6 月）帳單應繳金額為 NT$8,230，已完成繳款。

[用戶] 有哪些大筆消費？     ← AI 理解「大筆消費」= 上個月交易明細
[AI 呼叫] → GET /accounts/transactions?month=2026-06&min_amount=3000
[AI 回覆] 上個月 $3,000 以上的消費紀錄...
```

---

### 3.4 UC-03：信用卡掛失（Workflow Mode）

**完整五步驟流程**：

```
[用戶] 我的信用卡遺失了

[意圖分類] → WORKFLOW / report_card_loss
[Workflow 啟動] → Step 1

━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1：身分確認
━━━━━━━━━━━━━━━━━━━━━━━━

[AI]
了解，我將立即協助您辦理信用卡掛失。

為保護您的帳戶安全，請先確認您的身分。
請問您的身分證字號後四碼是？

[用戶] 1234

[API 呼叫] → POST /auth/verify { user_id, id_last4: "1234" }
[回傳] → { verified: true }

━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2：確認遺失卡片
━━━━━━━━━━━━━━━━━━━━━━━━

[AI]
身分確認成功 ✅

您目前持有以下信用卡，請問是哪張遺失了？

1️⃣ VISA 白金卡（卡號末四碼：1234）
2️⃣ Master 一般卡（卡號末四碼：5678）

請輸入 1 或 2，或直接說卡號末四碼。

[用戶] 1

━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3：執行掛失確認
━━━━━━━━━━━━━━━━━━━━━━━━

[AI]
您確定要掛失以下卡片嗎？

🔴 VISA 白金卡（末四碼：1234）

⚠️  掛失後此卡將立即停用，無法繼續消費。
    如需補發新卡，客服將與您聯繫安排。

請輸入「確認掛失」繼續，或「取消」放棄。

[用戶] 確認掛失

━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4：執行掛失 + 建立 Ticket
━━━━━━━━━━━━━━━━━━━━━━━━

[API 呼叫 1] → POST /cards/block { card_id: "card_1234" }
[回傳] → { success: true, blocked_at: "2026-07-06T14:32:00" }

[API 呼叫 2] → POST /tickets {
  type: "card_loss",
  card_id: "card_1234",
  user_id: "user_001"
}
[回傳] → { ticket_id: "T-20260706-001" }

[AI]
✅ 掛失完成！

VISA 白金卡（末四碼：1234）已於 2026/07/06 14:32 成功掛失。
卡片已立即停用，請放心。

📋 服務單號：#T-20260706-001
   客服將於 1 個工作日內與您聯繫補發新卡事宜。

━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5：後續說明 + 詢問是否轉接
━━━━━━━━━━━━━━━━━━━━━━━━

[AI]
📌 後續注意事項：
• 如有未授權消費，請撥打 0800-XXX-XXX 申請爭議款項
• 補發新卡預計 5-7 個工作日寄達
• 緊急用卡需求可申請臨時卡

需要立即轉接客服人員嗎？還是還有其他問題？

[用戶] 不用了，謝謝

[AI]
好的，掛失手續已完成。祝您平安，若有任何需要隨時可以詢問！
```

**中途取消流程**：

```
[用戶] 等等，我取消

[Workflow] → 偵測到「取消」關鍵字

[AI]
好的，已取消掛失流程，您的卡片狀態維持不變。

如果之後需要辦理掛失，隨時告訴我。
還有其他問題嗎？
```

**身分驗證失敗**：

```
[用戶] 5678  ← 錯誤的身分證後四碼

[API 呼叫] → 驗證失敗，剩餘嘗試次數：2

[AI]
抱歉，身分驗證失敗。請再確認您的身分證字號後四碼。
（剩餘嘗試次數：2 次）

--- 第三次失敗後 ---

[AI]
因多次驗證失敗，為保護您的帳戶安全，
將為您轉接客服人員協助辦理。

📞 客服電話：0800-XXX-XXX
🕐 服務時間：週一至週五 09:00-17:00

已建立服務單 #T-20260706-002，方便客服了解您的情況。
```

---

### 3.5 Human Handoff 流程

**主動要求真人**：

```
[用戶] 我要投訴！你們服務太差了！

[偵測] → ESCALATION / complaint + 情緒關鍵字

[AI]
非常抱歉讓您感到不便，我理解您的心情。

我將立即為您轉接客服人員，由真人專員協助處理您的問題。

📞 客服電話：0800-XXX-XXX
🕐 服務時間：週一至週五 09:00-17:00

非服務時間您可以：
• 留下您的聯繫方式，我們將主動回電
• 透過官方 APP 發送客服訊息

已為您建立服務單 #T-20260706-003，
客服人員接手後可立即了解您的情況。

再次為您帶來的不便深感抱歉。
```

**連續 Fallback 觸發**：

```
[Fallback Counter] → 已達 3 次

[AI]
很抱歉，我連續無法完整回答您的問題。

為了確保您得到準確的協助，建議轉接給我們的專業客服人員。

📞 客服電話：0800-XXX-XXX
🕐 服務時間：週一至週五 09:00-17:00

需要我幫您轉接嗎？
```

---

## 4. Fallback 策略

| 情況 | AI 行為 | 記錄 |
|------|---------|------|
| RAG Similarity < 0.7 | 誠實告知 + 提供客服電話 | ✅ 寫入 DB |
| 意圖不明確（第 1-2 次）| 反問釐清 | ❌ |
| 意圖連續 3 次不明 | 提供快速選單引導 | ✅ 寫入 DB |
| OUT_OF_SCOPE | Safety Guard 攔截 + 友善回導 | ❌ |
| API 呼叫失敗 | 告知系統暫時無法存取 + 替代方案 | ✅ 寫入 DB |
| Workflow 中途放棄 | 確認取消，保留狀態說明 | ❌ |

**快速選單引導（第 3 次意圖不明時使用）**：
```
讓我提供幾個常見的服務選項，請選擇最符合您需求的：

1️⃣ 查詢信用卡費用或優惠
2️⃣ 查詢本月帳單（需登入）
3️⃣ 信用卡掛失申請
4️⃣ 其他問題 → 轉接客服

請輸入數字 1-4
```

---

## 5. 語氣與語調規範

| 情境 | 語氣 | 範例 |
|------|------|------|
| 一般查詢 | 專業、友善、簡潔 | 「以下是您詢問的信用卡費用資訊：」|
| 緊急情況（掛失）| 積極、快速、安心 | 「我將立即協助您辦理掛失，請放心。」|
| 用戶情緒激動 | 同理、不辯解、主動解決 | 「非常抱歉讓您感到不便，我理解您的心情。」|
| 知識庫無答案 | 誠實、不猜測、給替代方案 | 「這個問題我目前無法確認，建議您...」|
| 系統錯誤 | 透明、道歉、提供替代 | 「系統暫時無法存取，請改用...」|

---

## 6. 對話記憶規則

- **保留範圍**：同一 session 最近 **10 輪**對話（5 輪用戶 + 5 輪 AI）
- **超出限制**：最舊的一輪自動移除（Rolling Window）
- **跨 session**：不保留（關閉視窗後重新開始）
- **Workflow State**：掛失流程的步驟狀態獨立存放（不佔用對話記憶 slot）

---

## 7. 中英文切換規則

| 情況 | 處理方式 |
|------|---------|
| 純中文輸入 | 中文回覆 |
| 純英文輸入 | 英文回覆 |
| 中英文混用（Chinglish）| 以主要語言判斷（中文字數 > 英文字數 → 中文）|
| 語言偵測失敗 | 預設繁體中文 |
| 同一 session 切換語言 | 每次重新偵測，隨時切換 |

---

*文件結束。下一步：Phase 3 Solution Architecture*
