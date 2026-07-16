"""
AI Banking Customer Assistant — Backend API
Sprint 4: FAQ + Account + Card Loss + Human Handoff + Dashboard
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
from backend.src.database import (create_ticket, get_stats, get_tickets,
                                   get_unresolved, init_db, log_unresolved)
from backend.src.mock_api.api import router as mock_api_router
from backend.src.mock_api.mock_data import get_user_by_id
from backend.src.rag.retriever import RAGRetriever

load_dotenv()

app = FastAPI(
    title="AI Banking Assistant API",
    description="XX Bank AI Customer Service — Sprint 4 (FAQ + Account + Card Loss + Handoff + Dashboard)",
    version="4.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(mock_api_router)

# ── Startup ────────────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    init_db()
    global retrievers
    retrievers = {
        "zh": RAGRetriever("zh", INDEX_DIR),
        "en": RAGRetriever("en", INDEX_DIR),
    }

# ── Config ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
KB_DIR = PROJECT_ROOT / "data" / "knowledge_base"
INDEX_DIR = PROJECT_ROOT / "data" / "faiss_index"
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1024))
MAX_HISTORY_TURNS = int(os.getenv("MAX_HISTORY_TURNS", 10))
MODEL = "claude-haiku-4-5"

retrievers: dict[str, RAGRetriever] = {}  # populated at startup

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
HANDOFF_KW   = ["投訴", "申訴", "真人", "客服人員", "我要告", "complaint", "speak to agent", "speak to human", "human agent", "real person"]
NEGATIVE_KW  = ["不對", "不是", "沒幫助", "幫不上", "沒有回答", "不是這樣", "還是不懂", "你搞錯了",
                 "wrong", "not helpful", "not what i asked", "didn't answer", "useless", "that's not right"]

def is_card_loss(text: str) -> bool:
    return any(kw in text.lower() for kw in CARD_LOSS_KW)

def is_handoff_trigger(text: str) -> bool:
    return any(kw in text.lower() for kw in HANDOFF_KW)

def is_negative_feedback(text: str) -> bool:
    return any(kw in text.lower() for kw in NEGATIVE_KW)

HANDOFF_MSG = {
    "zh": (
        "很抱歉我沒能完全解決您的問題。\n\n"
        "📞 **客服專線：0800-XXX-XXX**\n"
        "🕐 週一至週五 08:00–22:00\n\n"
        "緊急服務（掛失、帳戶凍結）：24 小時真人接聽，請選「緊急服務」。\n\n"
        "本次對話記錄已保存，客服人員可查閱。感謝您的耐心！"
    ),
    "en": (
        "I'm sorry I couldn't fully resolve your issue.\n\n"
        "📞 **Hotline: 0800-XXX-XXX**\n"
        "🕐 Mon–Fri 08:00–22:00\n\n"
        "Emergency (card loss, account freeze): 24/7 live agents — select 'Emergency Services'.\n\n"
        "This conversation has been saved for our team. Thank you for your patience!"
    ),
}

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
- Use ONLY the Retrieved Knowledge Chunks or User Account Data below
- If the chunks don't contain the answer, say so honestly and provide 0800-XXX-XXX
- Do NOT make up fees, rates, or rules not found in the chunks

## Human Handoff
If user mentions 投訴 申訴 真人 客服人員 complaint "human agent": provide hotline 0800-XXX-XXX immediately.

## Current User Account Data
{user_context}

## Retrieved Knowledge Base Chunks
{rag_context}
"""

def build_system_prompt(language: str, user_id: Optional[str], rag_context: str = "") -> str:
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
        rag_context=rag_context or "(No knowledge base chunks retrieved.)",
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
    fallback_count: int = 0       # consecutive unresolved turns, tracked by frontend
    force_handoff: bool = False   # frontend sends True when fallback_count >= 3

class ChatResponse(BaseModel):
    response: str
    language: str
    session_id: str
    workflow: WorkflowState = WorkflowState()
    is_negative_feedback: bool = False
    rag_sources: list[str] = []  # source file names used for this answer

# ── Chat Endpoint ──────────────────────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    language = detect_language(req.message)
    wf = req.workflow

    # ── Active card-loss workflow ─────────────────────────────────────────────
    if wf.step > 0:
        if not req.user_id:
            msg = "請先登入才能繼續掛失流程。" if language == "zh" else "Please log in to continue."
            return ChatResponse(response=msg, language=language, session_id=req.session_id)
        response_text, updated = card_loss_step(req.message, wf.model_dump(), req.user_id, language)
        return ChatResponse(
            response=response_text, language=language,
            session_id=req.session_id, workflow=WorkflowState(**updated),
        )

    # ── Human Handoff: keyword trigger ────────────────────────────────────────
    if is_handoff_trigger(req.message) or req.force_handoff:
        reason = "handoff_keyword" if is_handoff_trigger(req.message) else "fallback_threshold"
        log_unresolved(
            session_id=req.session_id, user_query=req.message,
            language=language, trigger_reason=reason, intent="escalation",
        )
        return ChatResponse(
            response=HANDOFF_MSG[language], language=language, session_id=req.session_id,
        )

    # ── Card loss intent: start workflow ──────────────────────────────────────
    if is_card_loss(req.message):
        if not req.user_id:
            msg = ("要辦理掛失，需要先登入才能驗證身分。請點側邊欄登入！"
                   if language == "zh" else "Please log in first to report a lost card.")
            return ChatResponse(response=msg, language=language, session_id=req.session_id)
        msg = ("好的，馬上協助您辦理掛失！\n\n為了保護帳戶安全，需要先確認身分。\n**請問您的身分證後四碼是？**"
               if language == "zh"
               else "I'll help you block the card right away!\n\nTo protect your account, I need to verify your identity.\n**What are the last 4 digits of your national ID?**")
        return ChatResponse(
            response=msg, language=language,
            session_id=req.session_id, workflow=WorkflowState(step=1),
        )

    # ── Negative feedback: log + still answer ─────────────────────────────────
    neg_fb = is_negative_feedback(req.message)
    if neg_fb:
        log_unresolved(
            session_id=req.session_id, user_query=req.message,
            language=language, trigger_reason="negative_feedback", intent="feedback",
        )

    # ── RAG Retrieval ─────────────────────────────────────────────────────────
    retriever = retrievers.get(language)
    rag_chunks: list[dict] = []
    rag_sources: list[str] = []

    if retriever and retriever.is_ready:
        rag_chunks = retriever.retrieve(req.message)
        rag_sources = list(dict.fromkeys(c["source"] for c in rag_chunks))  # dedup, order-preserving
        # Log unresolved if no chunk passes similarity threshold (FAQ miss)
        if not retriever.has_relevant_results(rag_chunks) and not req.user_id:
            log_unresolved(
                session_id=req.session_id, user_query=req.message,
                language=language, trigger_reason="rag_low_similarity", intent="faq",
                similarity_score=rag_chunks[0]["score"] if rag_chunks else None,
            )
        rag_context = retriever.format_context(rag_chunks)
    else:
        # Fallback: context stuffing (index not built yet)
        rag_context = KB[language]

    # ── Normal FAQ / Account query via Claude ─────────────────────────────────
    system_prompt = build_system_prompt(language, req.user_id, rag_context=rag_context)
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

    return ChatResponse(
        response=response_text, language=language,
        session_id=req.session_id, is_negative_feedback=neg_fb,
        rag_sources=rag_sources,
    )

# ── Data Endpoints ─────────────────────────────────────────────────────────────
@app.get("/tickets")
def list_tickets(user_id: Optional[str] = None, limit: int = 20):
    return get_tickets(user_id=user_id, limit=limit)

@app.get("/unresolved")
def list_unresolved(limit: int = 20):
    return get_unresolved(limit=limit)

@app.get("/stats")
def stats():
    return get_stats()

@app.get("/health")
def health():
    rag_status = {
        lang: retrievers[lang].is_ready if lang in retrievers else False
        for lang in ["zh", "en"]
    }
    return {
        "status": "ok",
        "sprint": 5,
        "mode": "RAG + account_query + card_loss + handoff + dashboard",
        "rag_index_ready": rag_status,
    }
