"""
LangGraph Nodes — Sprint 6 (Router/CardLoss/Handoff/FAQ/Logger), Sprint 7 (Account)

Sprint 6 moved Sprint 1-5's if/else `chat()` branches into a graph
without changing external behavior. Sprint 7 gave the Account Node a
real implementation: instead of stuffing the user's full account data
into the FAQ Node's system prompt, it now runs its own Claude call with
tools (get_account_balance / get_credit_card_bill / get_transactions)
and only fetches what the question actually needs. See docs/ADR.md
ADR-008 and docs/design_journal.md Sprint 7 entry for the reasoning.
"""

import json
from typing import Any

from ..card_loss_workflow import handle_step as card_loss_step
from ..database import log_unresolved
from ..nlp import is_account_query, is_card_loss, is_handoff_trigger, is_negative_feedback, detect_language
from ..prompts import HANDOFF_MSG, build_account_system_prompt, build_system_prompt
from .state import AgentState
from .tools import ACCOUNT_TOOLS, execute_tool

MAX_TOOL_ITERATIONS = 3

NOT_LOGGED_IN_ACCOUNT = {
    "zh": "要查詢帳務資訊，需要先登入喔！請點選側邊欄登入。",
    "en": "Please log in first to check your account information.",
}

TOOL_LOOP_FALLBACK = {
    "zh": "抱歉，這個查詢比較複雜，請稍後再試，或撥打客服專線 0800-XXX-XXX。",
    "en": "Sorry, this request is taking a bit long. Please try again or call 0800-XXX-XXX.",
}

# ── Router Node ──────────────────────────────────────────────────────────────

def router_node(state: AgentState) -> dict:
    message = state["user_message"]
    language = detect_language(message)

    # An in-progress card-loss workflow always continues, regardless of
    # what the user types next (mirrors Sprint 3's `if wf.step > 0` guard).
    if state.get("workflow_step", 0) > 0:
        return {"language": language, "intent": "card_loss"}

    if is_handoff_trigger(message) or state.get("force_handoff"):
        reason = "handoff_keyword" if is_handoff_trigger(message) else "fallback_threshold"
        return {"language": language, "intent": "handoff", "handoff_reason": reason}

    if is_card_loss(message):
        return {"language": language, "intent": "card_loss"}

    intent = "account" if is_account_query(message) else "faq"
    return {"language": language, "intent": intent}


# ── CardLoss Node ────────────────────────────────────────────────────────────

def card_loss_node(state: AgentState) -> dict:
    language = state["language"]
    message = state["user_message"]
    user_id = state.get("user_id")
    step = state.get("workflow_step", 0)
    data = state.get("workflow_data", {})

    if step > 0:
        if not user_id:
            msg = ("請先登入才能繼續掛失流程。" if language == "zh"
                   else "Please log in to continue.")
            return {"response": msg, "workflow_step": 0, "workflow_data": {}}
        response_text, updated = card_loss_step(message, {"step": step, "data": data}, user_id, language)
        return {"response": response_text, "workflow_step": updated["step"], "workflow_data": updated["data"]}

    # step == 0 → this turn is the trigger that opens the workflow
    if not user_id:
        msg = ("要辦理掛失，需要先登入才能驗證身分。請點側邊欄登入！"
               if language == "zh" else "Please log in first to report a lost card.")
        return {"response": msg}

    msg = ("好的，馬上協助您辦理掛失！\n\n為了保護帳戶安全，需要先確認身分。\n**請問您的身分證後四碼是？**"
           if language == "zh"
           else "I'll help you block the card right away!\n\nTo protect your account, I need to verify your identity.\n**What are the last 4 digits of your national ID?**")
    return {"response": msg, "workflow_step": 1, "workflow_data": {}}


# ── Handoff Node ─────────────────────────────────────────────────────────────

def handoff_node(state: AgentState) -> dict:
    language = state["language"]
    reason = state.get("handoff_reason", "handoff_keyword")
    return {
        "response": HANDOFF_MSG[language],
        "log_entries": [{"trigger_reason": reason, "intent": "escalation"}],
    }


# ── FAQ Node ─────────────────────────────────────────────────────────────────

def make_qa_node(client, retrievers: dict, kb: dict, model: str, max_tokens: int):
    def qa_node(state: AgentState) -> dict:
        language = state["language"]
        message = state["user_message"]
        user_id = state.get("user_id")

        log_entries: list[dict] = []
        neg_fb = is_negative_feedback(message)
        if neg_fb:
            log_entries.append({"trigger_reason": "negative_feedback", "intent": "feedback"})

        retriever = retrievers.get(language)
        rag_sources: list[str] = []
        if retriever and retriever.is_ready:
            rag_chunks = retriever.retrieve(message)
            rag_sources = list(dict.fromkeys(c["source"] for c in rag_chunks))
            if not retriever.has_relevant_results(rag_chunks) and not user_id:
                log_entries.append({
                    "trigger_reason": "rag_low_similarity",
                    "intent": "faq",
                    "similarity_score": rag_chunks[0]["score"] if rag_chunks else None,
                })
            rag_context = retriever.format_context(rag_chunks)
        else:
            rag_context = kb[language]

        system_prompt = build_system_prompt(language, user_id, rag_context=rag_context)
        messages: list[dict[str, Any]] = list(state.get("messages", []))
        messages.append({"role": "user", "content": message})

        result = client.messages.create(
            model=model, max_tokens=max_tokens, system=system_prompt, messages=messages
        )
        response_text = result.content[0].text

        return {
            "response": response_text,
            "is_negative_feedback": neg_fb,
            "rag_sources": rag_sources,
            "log_entries": log_entries,
        }

    return qa_node


# ── Account Node ─────────────────────────────────────────────────────────────

def make_account_node(client, model: str, max_tokens: int):
    def account_node(state: AgentState) -> dict:
        language = state["language"]
        user_id = state.get("user_id")

        if not user_id:
            return {"response": NOT_LOGGED_IN_ACCOUNT[language]}

        system_prompt = build_account_system_prompt(language)
        messages: list[dict[str, Any]] = list(state.get("messages", []))
        messages.append({"role": "user", "content": state["user_message"]})

        for _ in range(MAX_TOOL_ITERATIONS):
            result = client.messages.create(
                model=model, max_tokens=max_tokens, system=system_prompt,
                messages=messages, tools=ACCOUNT_TOOLS,
            )
            if result.stop_reason != "tool_use":
                text = "".join(b.text for b in result.content if b.type == "text")
                return {"response": text}

            messages.append({"role": "assistant", "content": result.content})
            tool_results = []
            for block in result.content:
                if block.type == "tool_use":
                    output = execute_tool(block.name, block.input, user_id)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(output, ensure_ascii=False),
                    })
            messages.append({"role": "user", "content": tool_results})

        return {
            "response": TOOL_LOOP_FALLBACK[language],
            "log_entries": [{"trigger_reason": "tool_loop_exceeded", "intent": "account"}],
        }

    return account_node


# ── Logger Node ──────────────────────────────────────────────────────────────

def logger_node(state: AgentState) -> dict:
    for entry in state.get("log_entries", []):
        log_unresolved(
            session_id=state["session_id"],
            user_query=state["user_message"],
            language=state["language"],
            intent=entry.get("intent", "unknown"),
            trigger_reason=entry["trigger_reason"],
            similarity_score=entry.get("similarity_score"),
        )
    return {}
