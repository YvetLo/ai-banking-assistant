"""
AI Banking Customer Assistant — Backend API
Sprint 1: FAQ with Context Stuffing
"""

import os
import re
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langdetect import detect, LangDetectException
from pydantic import BaseModel

load_dotenv()

app = FastAPI(
    title="AI Banking Assistant API",
    description="XX Bank AI Customer Service — Sprint 1 (Context Stuffing FAQ)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
KB_DIR = PROJECT_ROOT / "data" / "knowledge_base"
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1024))
MAX_HISTORY_TURNS = int(os.getenv("MAX_HISTORY_TURNS", 10))
MODEL = "claude-haiku-4-5"

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── Knowledge Base (loaded once at startup) ────────────────────────────────────
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
    # Chinese characters take priority over langdetect (which misclassifies short Chinese texts)
    if re.search(r"[一-鿿㐀-䶿]", text):
        return "zh"
    try:
        lang = detect(text)
        return "zh" if lang in ("zh-tw", "zh-cn", "zh") else "en"
    except LangDetectException:
        return "zh"

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

## Answer Rules
- Use ONLY the Knowledge Base below — do not invent numbers or facts
- If the answer is not in the Knowledge Base: say so honestly, provide hotline 0800-XXX-XXX
- Keep answers concise: 3–5 sentences for simple queries; use bullet points or tables for lists
- Cite the section name when helpful (e.g., "根據信用卡費用說明：")

## Human Handoff Trigger
If user says any of: 投訴 申訴 真人 客服人員 complaint "speak to agent" "human" — immediately provide:
- Hotline: 0800-XXX-XXX (Mon–Fri 08:00–22:00)
- Emergency (card loss): available 24/7

## Knowledge Base
{knowledge_base}
"""

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

def build_system_prompt(language: str) -> str:
    cfg = CONFIGS[language]
    return SYSTEM_TEMPLATE.format(
        lang_name=cfg["lang_name"],
        out_of_scope=cfg["out_of_scope"],
        disclaimer=cfg["disclaimer"],
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

class ChatResponse(BaseModel):
    response: str
    language: str
    session_id: str

# ── Endpoints ──────────────────────────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    language = detect_language(req.message)
    system_prompt = build_system_prompt(language)

    # Rolling window: keep last N turns
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
        "sprint": 1,
        "mode": "context_stuffing",
        "kb_zh_chars": len(KB["zh"]),
        "kb_en_chars": len(KB["en"]),
    }
