"""
Agent State — Sprint 6 (LangGraph)
See docs/agent_design.md §2 for the field-by-field spec this mirrors.
"""

from typing import Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    # Conversation
    messages: list[dict]          # prior turns, {"role": "user"/"assistant", "content": str}
    user_message: str             # current turn's raw input

    # Intent & language
    intent: str                   # "faq" / "account" / "card_loss" / "handoff"
    language: str                 # "zh" or "en"

    # Identity
    user_authenticated: bool
    user_id: Optional[str]

    # Card-loss workflow (0=not started, 1=verify, 2=select card, 3=confirm, 4=done)
    workflow_step: int
    workflow_data: dict[str, Any]

    # Escalation
    fallback_count: int
    force_handoff: bool
    handoff_reason: str            # set by Router, consumed by Handoff Node

    # Session
    session_id: str

    # RAG
    rag_sources: list[str]

    # Logger Node input — each dict: {trigger_reason, intent, similarity_score?}
    log_entries: list[dict]

    # Outputs
    response: str
    is_negative_feedback: bool
