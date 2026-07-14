# RAG Answer Generation Prompt
# AI Banking Customer Assistant

**版本**：v1.0
**適用 Sprint**：Sprint 5+（Sprint 1-4 使用 Context Stuffing 版本）

---

## 設計原則

RAG Answer Prompt 的核心約束：
1. **Context-only**：只根據 Retrieved Context 回答，不使用訓練知識補充
2. **Source Citation**：回答附上來源文件名稱（增加可信度，面試加分項）
3. **Honest Fallback**：Context 無法回答時，明確說不知道而非猜測
4. **Disclaimer Injection**：財務數字由程式碼強制附加，不依賴 AI

---

## RAG Answer Prompt（完整版）

```
You are an AI banking assistant answering customer questions based STRICTLY on the provided knowledge base excerpts.

## Core Rule
Answer ONLY using information from the Context below.
If the Context does not contain enough information to answer, say so clearly.
Do NOT use your general knowledge to fill in gaps.
Do NOT fabricate numbers, rates, dates, or product details.

## Response Format
- Use the user's language ({language}: Traditional Chinese or English)
- Be concise: 3-5 sentences for simple questions
- Use bullet points or tables for comparisons or multiple items
- End with "Source: [filename]" on a new line
- If multiple sources were used: "Sources: [file1], [file2]"

## Context (Retrieved Knowledge Base Excerpts)
Source 1: {source_1_filename}
---
{source_1_content}
---

Source 2: {source_2_filename}
---
{source_2_content}
---

Source 3: {source_3_filename}
---
{source_3_content}
---

## User Question
{user_question}

## Conversation History (Last 3 Turns)
{conversation_history}

## Instructions
1. Read all Context excerpts carefully
2. Identify which excerpt(s) contain relevant information
3. Synthesize a clear, accurate answer in {language}
4. If the information is in the Context: answer confidently and cite the source
5. If the information is NOT in the Context: respond with the Fallback Template below

## Fallback Template (use when Context is insufficient)
繁體中文: 「很抱歉，我的知識庫目前沒有關於這個問題的完整資訊。建議您撥打客服專線 0800-XXX-XXX，或前往 XX 銀行官網查詢。」
English: "I'm sorry, my knowledge base doesn't have complete information on this question. Please call our hotline at 0800-XXX-XXX or visit the XX Bank website."
```

---

## Sprint 1-4 Context Stuffing 版本

Sprint 1 使用時，`{source_N_content}` 直接替換為整份 FAQ 文件內容：

```python
def build_context_stuffing_prompt(user_question: str, language: str) -> str:
    """Sprint 1-4: Load all FAQ files into context."""

    kb_dir = Path("data/knowledge_base") / language
    all_content = []

    for md_file in sorted(kb_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        all_content.append(f"## {md_file.name}\n{content}")

    combined_context = "\n\n---\n\n".join(all_content)

    return RAG_ANSWER_PROMPT_STUFFING.format(
        language="繁體中文" if language == "zh" else "English",
        knowledge_base=combined_context,
        user_question=user_question,
        conversation_history="..."
    )
```

---

## Sprint 5+ RAG 版本

```python
def build_rag_prompt(
    user_question: str,
    retrieved_chunks: list[dict],  # [{"source": "file.md", "text": "...", "score": 0.85}]
    language: str,
    conversation_history: list[dict]
) -> str:
    """Sprint 5+: Build prompt with FAISS-retrieved chunks."""

    # Top-3 chunks（已由 FAISS 排序）
    sources = []
    for i, chunk in enumerate(retrieved_chunks[:3], 1):
        sources.append({
            f"source_{i}_filename": chunk["source"],
            f"source_{i}_content": chunk["text"]
        })

    # 對話歷史（最近 3 輪）
    recent = conversation_history[-6:]  # 3 問 3 答
    history_str = "\n".join([
        f"{'用戶' if m['role'] == 'user' else 'AI'}: {m['content']}"
        for m in recent
    ])

    return RAG_ANSWER_PROMPT.format(
        language="繁體中文" if language == "zh" else "English",
        source_1_filename=sources[0]["source_1_filename"] if len(sources) > 0 else "N/A",
        source_1_content=sources[0]["source_1_content"] if len(sources) > 0 else "（無相關內容）",
        source_2_filename=sources[1]["source_2_filename"] if len(sources) > 1 else "N/A",
        source_2_content=sources[1]["source_2_content"] if len(sources) > 1 else "（無相關內容）",
        source_3_filename=sources[2]["source_3_filename"] if len(sources) > 2 else "N/A",
        source_3_content=sources[2]["source_3_content"] if len(sources) > 2 else "（無相關內容）",
        user_question=user_question,
        conversation_history=history_str or "（無對話歷史）"
    )
```

---

## 回答品質評估標準

| 評估維度 | 定義 | 衡量方式 |
|---------|------|---------|
| **Faithfulness** | 回答完全基於 Context，無額外編造 | 人工比對 Context vs 回答 |
| **Relevance** | 回答確實回應了用戶問題 | 人工評分 1-5 |
| **Source Attribution** | 每個回答都正確引用來源文件 | 自動比對 source 欄位 |
| **Language Consistency** | 回答語言與用戶輸入一致 | 自動偵測 |
| **Disclaimer Presence** | 財務數字回答有附 Disclaimer | 自動比對字串 |

**目標**：Sprint 5 完成後，Faithfulness > 0.9（10 個測試問題中 9 個無幻覺）

---

## 測試案例

### 測試 1：Context 有足夠資訊

輸入問題：「信用卡年費多少？」
Retrieved Context：包含 credit_card_fees.md 中的年費表格

預期輸出（中文）：
```
XX 銀行信用卡年費依卡別而異：
- 一般卡：年費 NT$800，每年消費滿 3 次免年費
- 白金卡：年費 NT$3,500，首年免年費
- 無限卡：年費 NT$12,000，持卡人另享機場接送等禮遇

以上費率以官網公告及您的持卡合約為準。

來源：credit_card_fees.md
```

---

### 測試 2：Context 無相關資訊

輸入問題：「你們有外幣帳戶嗎？」
Retrieved Context：credit_card_fees.md, account_services.md（均無外幣帳戶資訊）
Similarity scores：全部 < 0.7

預期輸出（中文）：
```
很抱歉，我的知識庫目前沒有關於外幣帳戶的完整資訊。
建議您撥打客服專線 0800-XXX-XXX，或前往 XX 銀行官網查詢最新服務項目。
```

---

### 測試 3：多輪對話上下文理解

第一輪：「ATM 每天可以提多少錢？」→ AI 回答每日提款上限 NT$20,000
第二輪：「那跨行的話？」

預期行為：AI 理解「那」指的是「跨行提款限額」，從 `atm_services.md` 中找到跨行限額並回答，而不是重新解讀為新問題。
