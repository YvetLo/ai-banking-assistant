"""
AI Banking Customer Assistant — Backend API
Sprint 2: Account Query + Mock Banking API
"""

import os
import re
from pathlib import Path
from typing import Optional

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langdetect import detect, LangDetectException
from pydantic import BaseModel

from backend.src.mock_api.api import router as mock_api_router
from backend.src.mock_api.mock_data import get_user_by_id

load_dotenv()

app = FastAPI(
    title="AI Banking Assistant API",
    description="XX Bank AI Customer Service — Sprint 2 (FAQ + Account Query)",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mock_api_router)

# ── Config ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
KB_DIR = PROJECT_ROOT / "data" / "knowledge_base"
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1024))
MAX_HISTORY_TURNS = int(os.getenv("MAX_HISTORY_TURNS", 10))
MODEL = "claude-haiku-4-5"

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── Knowledge Base ─────────────────────────────────────────────────────────────
def load_knowledge_base(language: str) -> str:
    lang_dir = KB_DIR / language
    if not lang_dir.exists():
        return ""
    sections = []
    for md_file in sorted(lang_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        sections.append(f"=== {md_file.stem} ===\n{content}")
    return "\n\n".join(sections)

KB = {"zh": load_knowledge_base("zh"), "en": load_knowledge_base("en")}

# ── Language Detection ─────────────────────────────────────────────────────────
def detect_language(text: str) -> str:
    if re.search(r"[一-鿿㐀-䶿]", text):
        return "zh"
    try:
        lang = detect(text)
        return "zh" if lang in ("zh-tw", "zh-cn", "zh") else "en"
    except LangDetectException:
        return "zh"

# ── User Context Formatter ─────────────────────────────────────────────────────
def format_user_context(user: dict, language: str) -> str:
    """Format user account data for injection into system prompt."""
    if language == "zh":
        lines = [f"【已登入用戶】{user['name']}"]

        for acc_type, acc in user.get("accounts", {}).items():
            type_name = {"savings": "存款帳戶", "checking": "活期帳戶", "fixed_deposit": "定存帳戶"}.get(acc_type, acc_type)
            extra = f"（到期 {acc.get('maturity_date', '')}，利率 {acc.get('interest_rate', '')}）" if acc_type == "fixed_deposit" else ""
            lines.append(f"• {type_name}（{acc['account_no']}）：NT${acc['balance']:,} {extra}".strip())

        for card in user.get("cards", []):
            status = "正常" if card["status"] == "active" else "已掛失"
            lines.append(f"• {card['type']}（末碼 {card['last4']}）：{status}，額度 NT${card['credit_limit']:,}，可用 NT${card['available_credit']:,}")

        current = user.get("bill", {}).get("current_month", {})
        if current:
            lines.append(f"• 本月帳單：應繳 NT${current['due_amount']:,}，截止日 {current['due_date']}，最低應繳 NT${current['min_payment']:,}")

        last = user.get("bill", {}).get("last_month", {})
        if last:
            paid = f"已繳（{last.get('paid_date', '')}）" if last.get("paid") else "未繳"
            lines.append(f"• 上月帳單：NT${last['due_amount']:,}，{paid}")

        txns = user.get("recent_transactions", [])[:5]
        if txns:
            lines.append("• 近期交易（最新 5 筆）：")
            for t in txns:
                sign = "+" if t["amount"] > 0 else ""
                lines.append(f"  {t['date']} {t['description']}：{sign}NT${t['amount']:,}")

        return "\n".join(lines)

    else:  # English
        lines = [f"[Authenticated User] {user['name']}"]

        for acc_type, acc in user.get("accounts", {}).items():
            type_name = {"savings": "Savings", "checking": "Checking", "fixed_deposit": "Fixed Deposit"}.get(acc_type, acc_type)
            extra = f"(matures {acc.get('maturity_date', '')}, rate {acc.get('interest_rate', '')})" if acc_type == "fixed_deposit" else ""
            lines.append(f"• {type_name} ({acc['account_no']}): NT${acc['balance']:,} {extra}".strip())

        for card in user.get("cards", []):
            status = "Active" if card["status"] == "active" else "Blocked"
            lines.append(f"• {card['type']} (last 4: {card['last4']}): {status}, limit NT${card['credit_limit']:,}, available NT${card['available_credit']:,}")

        current = user.get("bill", {}).get("current_month", {})
        if current:
            lines.append(f"• Current bill: NT${current['due_amount']:,} due {current['due_date']}, min payment NT${current['min_payment']:,}")

        last = user.get("bill", {}).get("last_month", {})
        if last:
            paid = f"Paid ({last.get('paid_date', '')})" if last.get("paid") else "Unpaid"
            lines.append(f"• Last month bill: NT${last['due_amount']:,}, {paid}")

        txns = user.get("recent_transactions", [])[:5]
        if txns:
            lines.append("• Recent transactions (last 5):")
            for t in txns:
                sign = "+" if t["amount"] > 0 else ""
                lines.append(f"  {t['date']} {t['description']}: {sign}NT${t['amount']:,}")

        return "\n".join(lines)

# ── System Prompt ──────────────────────────────────────────────────────────────
SYSTEM_TEMPLATE = """\
You are an intelligent customer service assistant for "XX Bank" (XX 銀行 AI 客服助理).

## Language Rule
Respond ENTIRELY in {lang_name}. Never mix languages.

## Scope Boundaries
You ONLY answer questions about XX Bank services:
credit cards, accounts, transfers, ATMs, loans, digital banking, branch services.

For ANY question outside banking scope, respond exactly:
{out_of_scope}

## Disclaimer Rule
For ANY response mentioning interest rates, fees, limits, or specific financial figures,
end your response with this line:
{disclaimer}

## Tone & Style
You are a friendly, real bank counter staff — speak like a person, not a document.
- Use natural, everyday spoken language (口語白話). Write how you would actually say it out loud.
- Keep it short: for simple questions, 1–3 sentences is ideal. Don't pad answers unnecessarily.
- Lead with action or answer directly. Example:
    Customer: 我要掛失卡片  →  AI: 好的，我立即協助您掛失！
    Customer: 年費多少？    →  AI: 白金卡年費是 NT$3,500，首年免費。
- NEVER start with a markdown heading (no # ## ### at the beginning)
- NEVER use stiff openers like「根據您的提問」「您好，感謝您的詢問」
- Use bullet points or a table ONLY when listing 3+ comparable items (e.g., multiple card tiers)
- For English: same rules — casual, direct, friendly customer service tone

## Answer Rules
- Use ONLY the Knowledge Base or the User Account Data below — do not invent numbers or facts
- If the answer is not available: say so honestly, provide hotline 0800-XXX-XXX

## Human Handoff Trigger
If user says any of: 投訴 申訴 真人 客服人員 complaint "speak to agent" "human" — immediately provide:
- Hotline: 0800-XXX-XXX (Mon–Fri 08:00–22:00)
- Emergency (card loss): available 24/7

## Current User Account Data
{user_context}

## Knowledge Base
{knowledge_base}
"""

NOT_LOGGED_IN = {
    "zh": "用戶尚未登入。若有人詢問個人帳務（餘額、帳單、消費明細），請告知需要先登入，並引導他們點選登入按鈕，同時提供繼續回答一般 FAQ 問題。",
    "en": "User is NOT logged in. If asked about personal account data (balance, bill, transactions), tell them they need to log in first, and offer to help with general FAQ questions instead.",
}

CONFIGS = {
    "zh": {
        "lang_name": "繁體中文",
        "out_of_scope": "「很抱歉，這個問題超出我的服務範圍。如需協助，請撥打客服專線 0800-XXX-XXX。」",
        "disclaimer": "⚠️ 以上資訊僅供參考，實際費率及費用以官網公告或持卡合約為準。",
    },
    "en": {
        "lang_name": "English",
        "out_of_scope": '"I\'m sorry, this question is outside my service scope. Please call our hotline at 0800-XXX-XXX."',
        "disclaimer": "⚠️ The above is for reference only. Actual rates and fees are subject to official announcements and your agreement.",
    },
}

def build_system_prompt(language: str, user_id: Optional[str] = None) -> str:
    cfg = CONFIGS[language]

    if user_id:
        user = get_user_by_id(user_id)
        user_context = format_user_context(user, language) if user else NOT_LOGGED_IN[language]
    else:
        user_context = NOT_LOGGED_IN[language]

    return SYSTEM_TEMPLATE.format(
        lang_name=cfg["lang_name"],
        out_of_scope=cfg["out_of_scope"],
        disclaimer=cfg["disclaimer"],
        user_context=user_context,
        knowledge_base=KB[language],
    )

# ── Request / Response Models ──────────────────────────────────────────────────
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    session_id: str
    history: list[Message] = []
    user_id: Optional[str] = None  # set after login

class ChatResponse(BaseModel):
    response: str
    language: str
    session_id: str

# ── Endpoints ──────────────────────────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    language = detect_language(req.message)
    system_prompt = build_system_prompt(language, req.user_id)

    history_window = req.history[-(MAX_HISTORY_TURNS * 2):]
    messages = [{"role": m.role, "content": m.content} for m in history_window]
    messages.append({"role": "user", "content": req.message})

    try:
        result = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=messages,
        )
        response_text = result.content[0].text
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Claude API error: {e}")

    return ChatResponse(
        response=response_text,
        language=language,
        session_id=req.session_id,
    )

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "sprint": 2,
        "mode": "context_stuffing + account_query",
        "kb_zh_chars": len(KB["zh"]),
        "kb_en_chars": len(KB["en"]),
    }
