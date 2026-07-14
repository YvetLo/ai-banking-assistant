# Safety Guard Prompt
# AI Banking Customer Assistant

**版本**：v1.0
**用途**：防止 AI 回答範圍外問題、避免幻覺、保護用戶資安

---

## 安全設計的三層架構

```
Layer 1：System Prompt 規則
  → AI 被告知「不能做什麼」

Layer 2：Intent-level 攔截
  → out_of_scope / unclear → 直接拒絕，不進 LLM 回答流程

Layer 3：Output 後處理（未來版本）
  → 掃描回答中是否包含不應出現的資訊
```

---

## 攔截分類

### A. 範圍外問題（Out of Scope）

完全不回答，直接給拒絕訊息。

**攔截關鍵字（繁體中文）**：
- 股票、基金、外匯投資、加密貨幣、幣圈
- 稅務申報、報稅、退稅
- 醫療、法律諮詢
- 情感諮詢、心理輔導
- 任何競爭銀行的產品比較

**攔截關鍵字（英文）**：
- stocks, investment, crypto, forex trading
- tax filing, tax advice
- medical, legal advice
- competitor bank comparison

**拒絕訊息模板**：
```
繁體中文：
「很抱歉，這個問題超出我的服務範圍。我主要協助 XX 銀行的信用卡、
帳戶、轉帳及數位銀行相關問題。如需其他協助，請撥打客服專線 0800-XXX-XXX。」

English:
"I'm sorry, this question is outside my service scope. I'm here to help
with XX Bank's credit cards, accounts, transfers, and digital banking.
For other inquiries, please call 0800-XXX-XXX."
```

---

### B. 敏感資訊保護

**絕不詢問**（即使對話流程需要）：
- 完整身分證字號（只詢問後 4 碼）
- 完整信用卡號碼（只詢問後 4 碼）
- 網路銀行密碼、PIN 碼
- OTP 驗證碼

**用戶主動提供敏感資訊時**：
```
繁體中文：
「感謝您的信任。為保護您的帳戶安全，請避免在對話中提供完整的[身分證號/信用卡號]。
我只需要後四碼即可完成驗證。」

English:
"Thank you for your trust. For your account security, please avoid sharing your
full [ID number/card number] in this chat. I only need the last 4 digits for verification."
```

---

### C. 金融建議防護（Disclaimer 強制觸發）

以下意圖觸發時，**回答末尾必須加 Disclaimer**（不依賴 AI 自行判斷）：

| 意圖 | Disclaimer 類型 |
|------|----------------|
| `loan_info` | 「以上資訊僅供參考，不構成財務建議，實際申辦資格及利率請洽分行。」|
| `credit_card_fee` | 「實際費率以官網公告及您的持卡合約為準。」|
| `account_rules` | 「存款利率以官網公告為準，如有變動恕不另行通知。」|
| 任何涉及數字的回答 | 「以上數據均為參考資訊，請以官方公告為準。」|

**實作方式**（程式碼層面強制插入）：

```python
DISCLAIMER_MAP = {
    "loan_info": {
        "zh": "\n\n⚠️ 以上資訊僅供參考，不構成財務建議。實際申辦資格、利率及條件依銀行審核結果為準，建議親洽分行或致電客服詳細諮詢。",
        "en": "\n\n⚠️ The above is for reference only and does not constitute financial advice. Actual eligibility, rates, and terms are subject to bank review. We recommend visiting a branch or calling customer service."
    },
    "credit_card_fee": {
        "zh": "\n\n📋 實際費率及優惠條件以官網公告及您的持卡合約為準，如有異動恕不另行通知。",
        "en": "\n\n📋 Actual rates and benefits are subject to official announcements and your cardholder agreement."
    },
    "default": {
        "zh": "\n\n以上資訊僅供參考，詳情請以 XX 銀行官網公告為準。",
        "en": "\n\nThe above information is for reference only. Please refer to XX Bank's official announcements for details."
    }
}

def append_disclaimer(response: str, intent: str, language: str) -> str:
    disclaimer = DISCLAIMER_MAP.get(intent, DISCLAIMER_MAP["default"])
    return response + disclaimer[language]
```

---

### D. 詐騙情境偵測

銀行 AI 本身就是詐騙攻擊目標，需要偵測以下情境：

**高風險情境**：
- 用戶說「XX 銀行打電話給我，叫我轉帳到安全帳戶」
- 用戶說「警察說我帳戶涉案，要我先轉帳」
- 用戶說「你們的人說我中獎了，要我先付手續費」

**回應模板（強制插入，不讓 AI 自由發揮）**：
```
繁體中文：
「⚠️ 請注意！這很可能是詐騙！

XX 銀行絕對不會：
• 要求您透過 ATM 或轉帳到「安全帳戶」
• 以警察或政府機關名義要求您轉帳
• 要求您分期取款或購買禮品卡

請立即掛斷可疑來電，並撥打：
• 銀行官方客服：0800-XXX-XXX 確認
• 165 反詐騙專線
• 110 報警

我已記錄本次對話，您也可以到銀行臨櫃諮詢。」
```

**偵測觸發詞**（中文）：
`安全帳戶`, `涉嫌洗錢`, `凍結帳戶`, `轉帳解凍`, `配合調查`, `中獎`, `手續費`, `先匯款`

---

## Safety Guard Prompt（供 LLM 使用）

此 Prompt 作為每次生成回答前的 Pre-check：

```
Before generating a response, check if the user's message triggers any safety rules.

## Safety Check List

1. OUT OF SCOPE: Is this question related to banking services?
   - If NO → Return out_of_scope signal, do not answer

2. SENSITIVE INFO: Does the message contain full ID numbers, full card numbers, or passwords?
   - If YES → Acknowledge without repeating, remind user of best practices

3. FINANCIAL ADVICE: Does this involve recommending specific financial products?
   - If YES → Provide information only, append mandatory disclaimer

4. FRAUD PATTERN: Does the message describe someone asking them to transfer money or share OTPs?
   - If YES → Return anti-fraud warning immediately

## Output Signal
If any rule triggered: {"safety_triggered": true, "rule": "<rule_name>", "action": "<action>"}
If no rules triggered: {"safety_triggered": false}

User Message: {user_message}
Intent: {intent}
```

---

## 面試說法備忘

**問：如何防止 AI 回答有害內容？**
> 三層防護：System Prompt 設定行為規則、Intent-level 硬編碼攔截（out_of_scope 直接拒絕，不送 LLM）、財務資訊強制插入 Disclaimer（程式碼層面，不依賴 AI 判斷）。最高優先級的安全規則（如詐騙警告）完全繞過 LLM，直接返回硬編碼訊息。

**問：AI 幻覺怎麼辦？**
> 兩個機制：RAG 的 context-only Prompt（「只根據以下資訊回答，若無相關資訊請說不知道」）、Similarity Threshold 過濾（相似度 < 0.7 直接 Fallback，不嘗試猜測）。這樣 AI 的幻覺空間被限縮在「改寫知識庫內容」的範圍，比「憑空生成」風險低得多。
