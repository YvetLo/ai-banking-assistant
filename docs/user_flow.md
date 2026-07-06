# User Flow Diagram
# AI Banking Customer Assistant

| 欄位 | 內容 |
|------|------|
| **文件版本** | v1.0 |
| **建立日期** | 2026-07-06 |
| **格式說明** | Mermaid 語法（可在 GitHub 或 mermaid.live 直接渲染） |

---

## 1. 整體系統流程

```mermaid
flowchart TD
    A([用戶進入聊天介面]) --> B[顯示開場白]
    B --> C[用戶輸入訊息]
    C --> D{語言偵測}
    D -->|中文| E[路由中文知識庫]
    D -->|英文| F[路由英文知識庫]
    E & F --> G{Safety Guard\n是否為銀行相關？}
    G -->|否 OUT_OF_SCOPE| H[友善拒絕\n回導主題]
    H --> C
    G -->|是| I{意圖分類\nIntent Router}
    I -->|FAQ| J[UC-01 FAQ 流程]
    I -->|ACCOUNT| K[UC-02 帳務查詢流程]
    I -->|WORKFLOW| L[UC-03 掛失 Workflow]
    I -->|ESCALATION| M[Human Handoff]
    J & K & L --> N{用戶滿意？}
    N -->|是| O[繼續對話]
    O --> C
    N -->|否 第3次| M
    M --> P([服務單建立\n對話結束])
```

---

## 2. UC-01：FAQ 查詢流程

```mermaid
flowchart TD
    A([用戶輸入問題]) --> B[FAISS 向量搜尋\nTop-K=3]
    B --> C{Similarity Score}
    C -->|≥ 0.7 命中| D[Claude 生成回答\n附來源文件]
    C -->|< 0.7 未命中| E[Fallback\n記錄至 DB]
    D --> F{涉及利率或費用？}
    F -->|是| G[自動附加\n免責聲明]
    F -->|否| H[直接回覆]
    G & H --> I[詢問：還有其他問題嗎？]
    E --> J[提供客服電話\n引導替代方案]
    I & J --> K([等待下一輪輸入])
```

---

## 3. UC-02：帳務查詢流程

```mermaid
flowchart TD
    A([用戶查詢帳務]) --> B{用戶是否已登入？}
    B -->|未登入| C[提示登入\n提供登入引導]
    C --> D([等待用戶登入])
    B -->|已登入| E{意圖細分}
    E -->|查帳單 check_bill| F[API: GET /accounts/bill]
    E -->|查餘額 check_balance| G[API: GET /accounts/balance]
    E -->|查交易 check_transactions| H[API: GET /accounts/transactions]
    F & G & H --> I{API 回應}
    I -->|成功| J[Claude 整理\n成自然語言]
    I -->|失敗| K[告知系統暫時無法存取\n記錄至 DB]
    J --> L[回覆用戶\n詢問是否需要更多查詢]
    K --> M[提供替代方案\n如行動 APP]
    L & M --> N([等待下一輪輸入])
```

---

## 4. UC-03：信用卡掛失 Workflow

```mermaid
flowchart TD
    A([用戶回報遺失]) --> B[Workflow 啟動\nStep 1: 身分確認]
    B --> C[詢問身分證後四碼]
    C --> D{API 驗證身分}
    D -->|驗證失敗| E{失敗次數}
    E -->|< 3 次| F[提示重試\n告知剩餘次數]
    F --> C
    E -->|≥ 3 次| G[觸發 Human Handoff\n建立 Ticket]
    D -->|驗證成功| H[Step 2: 列出持有卡片]
    H --> I[用戶選擇遺失卡片]
    I --> J[Step 3: 再次確認掛失]
    J --> K{用戶確認}
    K -->|取消| L[終止流程\n告知卡片狀態未變]
    K -->|確認掛失| M[Step 4: API 執行掛失\nPOST /cards/block]
    M --> N[API: 建立 Ticket\nPOST /tickets]
    N --> O[Step 5: 顯示服務單號\n說明後續流程]
    O --> P{用戶需要轉接？}
    P -->|需要| G
    P -->|不需要| Q([流程結束\n繼續一般對話])
    L --> Q
```

---

## 5. Human Handoff 流程

```mermaid
flowchart TD
    A([觸發 Human Handoff]) --> B{觸發原因}
    B -->|用戶主動要求| C[立即回應\n同理用戶情緒]
    B -->|連續 Fallback x3| D[告知轉接原因\n道歉說明]
    B -->|Workflow 驗證失敗| E[解釋安全機制\n安撫用戶]
    B -->|Workflow 中途放棄| F[尊重用戶決定\n簡短說明]
    C & D & E & F --> G[API: 建立 Ticket\nPOST /tickets]
    G --> H[顯示：\n客服電話\n服務時間\n服務單號]
    H --> I{服務時間內？}
    I -->|是| J[可立即撥打]
    I -->|否| K[留言 or 等待回電]
    J & K --> L[記錄至 unresolved_queries DB]
    L --> M([對話結束])
```

---

## 6. 知識庫更新維運流程

```mermaid
flowchart TD
    A([unresolved_queries 累積]) --> B[每週 Dashboard 審查]
    B --> C{問題分類}
    C -->|知識庫缺漏| D[撰寫新 FAQ Markdown]
    C -->|範圍外問題| E[更新 Safety Guard 關鍵字]
    C -->|意圖分類錯誤| F[調整 Intent 關鍵字或 Prompt]
    D --> G[執行 rebuild_index.py\n重建 FAISS index]
    E & F --> H[更新設定檔]
    G & H --> I[測試：\n原本 Fallback 的問題\n現在能正確回答？]
    I -->|通過| J[部署更新]
    I -->|未通過| D
    J --> K[記錄改善效果\ndocs/sprint_retros/]
    K --> A
```

---

## 7. Session 狀態圖

```mermaid
stateDiagram-v2
    [*] --> Idle : 用戶開啟聊天

    Idle --> FAQ : 意圖=FAQ
    Idle --> AccountQuery : 意圖=ACCOUNT
    Idle --> CardLossWorkflow : 意圖=WORKFLOW
    Idle --> HandOff : 意圖=ESCALATION
    Idle --> Idle : OUT_OF_SCOPE（Safety Guard 攔截）

    FAQ --> Idle : 回答完成
    FAQ --> HandOff : 連續 Fallback x3

    AccountQuery --> Idle : 查詢完成
    AccountQuery --> Login : 未登入
    Login --> AccountQuery : 登入成功
    AccountQuery --> HandOff : API 持續失敗

    CardLossWorkflow --> VerifyIdentity : Step 1
    VerifyIdentity --> SelectCard : 驗證成功
    VerifyIdentity --> HandOff : 失敗 x3
    SelectCard --> ConfirmBlock : Step 3
    ConfirmBlock --> Blocked : 確認掛失
    ConfirmBlock --> Idle : 取消
    Blocked --> HandOff : 用戶要求轉接
    Blocked --> Idle : 流程完成

    HandOff --> [*] : 對話結束
```

---

*文件結束。下一步：Phase 3 Solution Architecture*
