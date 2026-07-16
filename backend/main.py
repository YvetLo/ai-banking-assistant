"""
AI Banking Customer Assistant — Backend API
Sprint 3: FAQ + Account Query + Card Loss Workflow + Tickets
"""

import os
import re
from pathlib import Path
from typing import Any, Optional

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langdetect import detect, LangDetectException
from pydantic import BaseModel

from backend.src.card_loss_workflow import handle_step as card_loss_step
from backend.src.database import create_ticket, get_tickets, init_db
from backend.src.mock_api.api import router as mock_api_router
from backend.src.mock_api.mock_data import get_user_by_id

load_dotenv()

app = FastAPI(
    title="AI Banking Assistant API",
    description="XX Bank AI Customer Service — Sprint 3 (FAQ + Account + Card Loss + Tickets)",
    version="3.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(mock_api_router)

# ── Startup ────────────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    init_db()

# ── Config ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
KB_DIR = PROJECT_ROOT / "data" / "knowledge_base"
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1024))
MAX_HISTORY_TURNS = int(os.getenv("MAX_HISTORY_TURNS", 10))
MODEL = "claude-haiku-4-5"

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── Knowledge Base ─────────────────────────────────────────────────────────────
def load_kb(language: str) -> str:
    lang_dir = KB_DIR / language
    if not lang_dir.exists():
        return ""
    return "\n\n".join(
        f"=== {f.stem} ===\n{f.read_text(encoding='utf-8')}"
        for f in sorted(lang_dir.glob("*.md"))
    )

KB = {"zh": load_kb("zh"), "en": load_kb("en")}

# ── Language Detection ─────────────────────────────────────────────────────────
def detect_language(text: str) -> str:
    if re.search(r"[一-鿿㐀-䶿]", text):
        return "zh"
    try:
        return "zh" if detect(text) in ("zh-tw", "zh-cn", "zh") else "en"
    except LangDetectException:
        return "zh"

# ── Intent Helpers ─────────────────────────────────────────────────────────────
CARD_LOSS_KW = ["掛失", "遺失", "不見了", "被偷", "lost card", "card lost", "stolen card", "block my card"]

def is_card_loss(text: str) -> bool:
    return any(kw in text.lower() for kw in CARD_LOSS_KW)

# ── User Context Formatter ─────────────────────────────────────────────────────
def format_user_context(user: dict, language: str) -> str:
    if language == "zh":
        lines = [f"【已登入用戶】{user['name']}"]
        for acc_type, acc in user.get("accounts", {}).items():
            label = {"savings": "存款", "checking": "活期", "fixed_deposit": "定存"}.get(acc_type, acc_type)
            extra = f"（到期 {acc.get('maturity_date','')}，利率 {acc.get('interest_rate','')}）" if acc_type == "fixed_deposit" else ""
            lines.append(f"• {label}（{acc['account_no']}）：NT${acc['balance']:,} {extra}".strip())
        for card in user.get("cards", []):
            status = "正常" if card["status"] == "active" else "已掛失"
            lines.append(f"• {card['type']}（末碼 {card['last4']}）：{status}，額度 NT${card['credit_limit']:,}，可用 NT${card['available_credit']:,}")
        cur = user.get("bill", {}).get("current_month", {})
        if cur:
            lines.append(f"• 本月帳單：應繳 NT${cur['due_amount']:,}，截止日 {cur['due_date']}，最低 NT${cur['min_payment']:,}")
        last = user.get("bill", {}).get("last_month", {})
        if last:
            paid = f"已繳（{last.get('paid_date','')}）" if last.get("paid") else "未繳"
            lines.append(f"• 上月帳單：NT${last['due_amount']:,}，{paid}")
        txns = user.get("recent_transactions", [])[:5]
        if txns:
            lines.append("• 近期交易：")
            for t in txns:
                sign = "+" if t["amount"] > 0 else ""
                lines.append(f"  {t['date']} {t['description']}：{sign}NT${t['amount']:,}")
        return "\n".join(lines)
    else:
        lines = [f"[Authenticated User] {user['name']}"]
        for acc_type, acc in user.get("accounts", {}).items():
            label = {"savings": "Savings", "checking": "Checking", "fixed_deposit": "Fixed Deposit"}.get(acc_type, acc_type)
            extra = f"(matures {acc.get('maturity_date','')}, rate {acc.get('interest_rate','')})" if acc_type == "fixed_deposit" else ""
            lines.append(f"• {label} ({acc['account_no']}): NT${acc['balance']:,} {extra}".strip())
        for card in user.get("cards", []):
            status = "Active" if card["status"] == "active" else "Blocked"
            lines.append(f"• {card['type']} (last 4: {card['last4']}): {status}, limit NT${card['credit_limit']:,}, avail NT${card['available_credit']:,}")
        cur = user.get("bill", {}).get("current_month", {})
        if cur:
            lines.append(f"• Current bill: NT${cur['due_amount']:,} due {cur['due_date']}, min NT${cur['min_payment']:,}")
        last = user.get("bill", {}).get("last_month", {})
        if last:
            paid = f"Paid ({last.get('paid_date','')})" if last.get("paid") else "Unpaid"
            lines.append(f"• Last month: NT${last['due_amount']:,}, {paid}")
        txns = user.get("recent_transactions", [])[:5]
        if txns:
            lines.append("• Recent transactions:")
            for t in txns:
                sign = "+" if t["amount"] > 0 else ""
                lines.append(f"  {t['date']} {t['description']}: {sign}NT${t['amount']:,}")
        return "\n".join(lines)

# ── System Prompt ──────────────────────────────────────────────────────────────
NOT_LOGGED_IN = {
    "zh": "用戶尚未登入。若問到個人帳務，告知需先登入並引導點選登入。",
    "en": "User is NOT logged in. For personal account queries, ask them to log in first.",
}

CONFIGS = {
    "zh": {
        "lang_name": "繁體中文",
        "out_of_scope": "「很抱歉，這個問題超出我的服務範圍。如需協助，請撥打客服專線 0800-XXX-XXX。」",
        "disclaimer": "⚠️ 以上資訊僅供參考，實際費率及費用以官網公告或持卡合約為準。",
    },
    "en": {
        "lang_name": "English",
        "out_of_scope": '"I\'m sorry, this is outside my service scope. Please call 0800-XXX-XXX."',
        "disclaimer": "⚠️ For reference only. Actual rates subject to official announcements and your agreement.",
    },
}

SYSTEM_TEMPLATE = """\
You are an intelligent customer service assistant for "XX Bank" (XX 銀行 AI 客服助理).

## Language Rule
Respond ENTIRELY in {lang_name}. Never mix languages.

## Scope Boundaries
You ONLY answer questions about XX Bank services: credit cards, accounts, transfers, ATMs, loans, digital banking, branch services.
For ANY out-of-scope question: {out_of_scope}

## Disclaimer Rule
For ANY response mentioning rates, fees, or financial figures, end with:
{disclaimer}

## Tone & Style
- Friendly, natural spoken language — like a real bank counter staff
- Lead with action or answer directly (e.g. 「好的，我馬上幫您查！」)
- NEVER start with a markdown heading
- NEVER use stiff openers like「根據您的提問」
- Tables/bullets only for 3+ comparable items; otherwise prose

## Answer Rules
- Use ONLY the Knowledge Base or User Account Data below
- If unavailable: say so honestly, provide 0800-XXX-XXX

## Human Handoff
If user mentions 投訴 申訴 真人 客服人員 complaint "human agent": provide hotline 0800-XXX-XXX immediately.

## Current User Account Data
{user_context}

## Knowledge Base
{knowledge_base}
"""

def build_system_prompt(language: str, user_id: Optional[str]) -> str:
    cfg = CONFIGS[language]
    if user_id:
        user = get_user_by_id(user_id)
        ctx = format_user_context(user, language) if user else NOT_LOGGED_IN[language]
    else:
        ctx = NOT_LOGGED_IN[language]
    return SYSTEM_TEMPLATE.format(
        lang_name=cfg["lang_name"],
        out_of_scope=cfg["out_of_scope"],
        disclaimer=cfg["disclaimer"],
        user_context=ctx,
        knowledge_base=KB[language],
    )

# ── Models ─────────────────────────────────────────────────────────────────────
class Message(BaseModel):
    role: str
    content: str

class WorkflowState(BaseModel):
    step: int = 0
    data: dict[str, Any] = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str
    history: list[Message] = []
    user_id: Optional[str] = None
    workflow: WorkflowState = WorkflowState()

class ChatResponse(BaseModel):
    response: str
    language: str
    session_id: str
    workflow: WorkflowState = WorkflowState()

# ── Chat Endpoint ──────────────────────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    language = detect_language(req.message)
    wf = req.workflow

    # ── Active workflow: route to state machine ──────────────────────────────
    if wf.step > 0:
        if not req.user_id:
            msg = "請先登入才能繼續掛失流程。" if language == "zh" else "Please log in to continue."
            return ChatResponse(response=msg, language=language, session_id=req.session_id)
        response_text, updated = card_loss_step(req.message, wf.model_dump(), req.user_id, language)
        return ChatResponse(
            response=response_text,
            language=language,
            session_id=req.session_id,
            workflow=WorkflowState(**updated),
        )

    # ── Card loss intent: start workflow ─────────────────────────────────────
    if is_card_loss(req.message):
        if not req.user_id:
            msg = ("要辦理掛失，需要先登入才能驗證身分。請點側邊欄登入！"
                   if language == "zh" else "Please log in first to report a lost card.")
            return ChatResponse(response=msg, language=language, session_id=req.session_id)
        msg = ("好的，馬上協助您辦理掛失！\n\n為了保護帳戶安全，需要先確認身分。\n**請問您的身分證後四碼是？**"
               if language == "zh"
               else "I'll help you block the card right away!\n\nFirst, I need to verify your identity.\n**What are the last 4 digits of your national ID?**")
        return ChatResponse(
            response=msg,
            language=language,
            session_id=req.session_id,
            workflow=WorkflowState(step=1),
        )

    # ── Normal FAQ / Account query via Claude ─────────────────────────────────
    system_prompt = build_system_prompt(language, req.user_id)
    history = req.history[-(MAX_HISTORY_TURNS * 2):]
    messages = [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": req.message})

    try:
        result = client.messages.create(
            model=MODEL, max_tokens=MAX_TOKENS, system=system_prompt, messages=messages
        )
        response_text = result.content[0].text
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return ChatResponse(response=response_text, language=language, session_id=req.session_id)

# ── Tickets Endpoint ───────────────────────────────────────────────────────────
@app.get("/tickets")
def list_tickets(user_id: Optional[str] = None, limit: int = 20):
    return get_tickets(user_id=user_id, limit=limit)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "sprint": 3,
        "mode": "context_stuffing + account_query + card_loss_workflow",
    }
