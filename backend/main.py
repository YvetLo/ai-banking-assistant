"""
AI Banking Customer Assistant — Backend API
Sprint 6: LangGraph state machine (Router → FAQ/Account/CardLoss/Handoff/Logger)
"""

import os
from pathlib import Path
from typing import Any, Optional

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.src.agent.graph import build_graph
from backend.src.agent.state import AgentState
from backend.src.database import (get_stats, get_tickets, get_unresolved, init_db)
from backend.src.mock_api.api import router as mock_api_router
from backend.src.prompts import KB
from backend.src.rag.retriever import RAGRetriever

load_dotenv()

app = FastAPI(
    title="AI Banking Assistant API",
    description="XX Bank AI Customer Service — Sprint 7 (LangGraph: Router/FAQ/Account(tool-calling)/CardLoss/Handoff/Logger)",
    version="7.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(mock_api_router)

# ── Config ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
INDEX_DIR = PROJECT_ROOT / "data" / "faiss_index"
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1024))
MAX_HISTORY_TURNS = int(os.getenv("MAX_HISTORY_TURNS", 10))
MODEL = "claude-haiku-4-5"

retrievers: dict[str, RAGRetriever] = {}  # populated at startup
agent_graph = None  # compiled LangGraph, populated at startup

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── Startup ────────────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    init_db()
    global retrievers, agent_graph
    retrievers = {
        "zh": RAGRetriever("zh", INDEX_DIR),
        "en": RAGRetriever("en", INDEX_DIR),
    }
    agent_graph = build_graph(client, retrievers, KB, MODEL, MAX_TOKENS)

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
    history = req.history[-(MAX_HISTORY_TURNS * 2):]
    initial_state: AgentState = {
        "user_message": req.message,
        "messages": [{"role": m.role, "content": m.content} for m in history],
        "user_id": req.user_id,
        "user_authenticated": req.user_id is not None,
        "session_id": req.session_id,
        "workflow_step": req.workflow.step,
        "workflow_data": req.workflow.data,
        "fallback_count": req.fallback_count,
        "force_handoff": req.force_handoff,
    }

    try:
        result = agent_graph.invoke(initial_state)
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return ChatResponse(
        response=result["response"],
        language=result["language"],
        session_id=req.session_id,
        workflow=WorkflowState(step=result.get("workflow_step", 0), data=result.get("workflow_data", {})),
        is_negative_feedback=result.get("is_negative_feedback", False),
        rag_sources=result.get("rag_sources", []),
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
        "sprint": 7,
        "mode": "LangGraph (Router -> FAQ/Account[tool-calling]/CardLoss/Handoff/Logger)",
        "rag_index_ready": rag_status,
    }
