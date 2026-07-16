"""
Credit card loss workflow — 4-step state machine.
Handles identity verification, card selection, confirmation, and execution.
"""

import re
from typing import Any

from .database import create_ticket
from .mock_api.mock_data import block_card, get_user_by_id, verify_identity

# ── Helpers ───────────────────────────────────────────────────────────────────

def _4digits(text: str) -> str | None:
    m = re.search(r"\b(\d{4})\b", text)
    return m.group(1) if m else None

def _is_cancel(text: str) -> bool:
    return any(w in text.lower() for w in ["取消", "算了", "不要了", "cancel", "stop", "quit"])

def _is_confirm(text: str) -> bool:
    return any(w in text.lower() for w in ["確認", "confirm", "yes", "是", "好", "ok", "對"])

def _match_card(text: str, cards: list[dict]) -> dict | None:
    text_lower = text.lower()
    # By number
    m = re.search(r"\b([1-9])\b", text_lower)
    if m:
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(cards):
            return cards[idx]
    # By last4
    m = re.search(r"\b(\d{4})\b", text)
    if m:
        for c in cards:
            if c["last4"] == m.group(1):
                return c
    # By type keyword
    kw_map = [("白金", "白金"), ("platinum", "Platinum"), ("無限", "無限"),
              ("infinite", "Infinite"), ("金卡", "金"), ("gold", "Gold"),
              ("一般", "一般"), ("standard", "Standard")]
    for kw, card_kw in kw_map:
        if kw in text_lower:
            for c in cards:
                if card_kw.lower() in c["type"].lower():
                    return c
    return None

def _fmt_cards(cards: list[dict], language: str) -> str:
    if language == "zh":
        return "\n".join(f"{i+1}. {c['type']}（末碼 {c['last4']}）" for i, c in enumerate(cards))
    return "\n".join(f"{i+1}. {c['type']} (last 4: {c['last4']})" for i, c in enumerate(cards))

# ── Workflow Entry Point ───────────────────────────────────────────────────────

def handle_step(
    message: str,
    workflow: dict[str, Any],
    user_id: str,
    language: str,
) -> tuple[str, dict[str, Any]]:
    """
    Process one workflow step.
    Returns: (response_text, updated_workflow_state)
    """
    step = workflow.get("step", 0)
    data = workflow.get("data", {})

    # Cancel at any step
    if _is_cancel(message):
        msg = ("好的，已取消掛失流程。有需要隨時告訴我！" if language == "zh"
               else "Card loss process cancelled. Let me know if you need help!")
        return msg, {"step": 0, "data": {}}

    # ── Step 1: Waiting for id_last4 ──────────────────────────────────────────
    if step == 1:
        id_last4 = _4digits(message)
        if not id_last4:
            msg = ("麻煩輸入身分證後四碼（4 位數字）喔！"
                   if language == "zh" else "Please enter the last 4 digits of your national ID.")
            return msg, workflow

        attempts = data.get("verify_attempts", 0) + 1
        if not verify_identity(user_id, id_last4):
            if attempts >= 3:
                msg = ("驗證失敗次數過多，請致電 0800-XXX-XXX 由真人客服協助掛失。"
                       if language == "zh" else "Too many failed attempts. Please call 0800-XXX-XXX.")
                return msg, {"step": 0, "data": {}}
            remaining = 3 - attempts
            msg = (f"後四碼不符，再試一次（剩 {remaining} 次機會）。"
                   if language == "zh" else f"Verification failed. Try again ({remaining} attempts left).")
            return msg, {"step": 1, "data": {"verify_attempts": attempts}}

        user = get_user_by_id(user_id)
        active = [c for c in user["cards"] if c["status"] == "active"]
        if not active:
            msg = ("您目前沒有有效的信用卡，無法辦理掛失。如有問題請電 0800-XXX-XXX。"
                   if language == "zh" else "No active cards found. Please call 0800-XXX-XXX.")
            return msg, {"step": 0, "data": {}}

        card_list = _fmt_cards(active, language)
        msg = (f"驗證成功！您有以下信用卡，請問哪張遺失了？\n\n{card_list}\n\n輸入編號或卡片名稱都可以。"
               if language == "zh"
               else f"Identity verified! Which card was lost?\n\n{card_list}\n\nEnter a number or card name.")
        return msg, {"step": 2, "data": {"cards": active}}

    # ── Step 2: Waiting for card selection ────────────────────────────────────
    if step == 2:
        cards = data.get("cards", [])
        selected = _match_card(message, cards)
        if not selected:
            card_list = _fmt_cards(cards, language)
            msg = (f"沒找到符合的卡片，請用編號或末四碼選擇：\n{card_list}"
                   if language == "zh"
                   else f"Couldn't identify the card. Please use the number or last 4 digits:\n{card_list}")
            return msg, workflow

        msg = (f"確認要掛失這張卡嗎？\n\n"
               f"🔒 **{selected['type']}（末碼 {selected['last4']}）**\n\n"
               f"⚠️ 掛失後立即停用，無法繼續消費。\n\n"
               f"請輸入「**確認**」繼續，或「**取消**」結束。"
               if language == "zh"
               else f"Confirm blocking this card?\n\n"
               f"🔒 **{selected['type']} (last 4: {selected['last4']})**\n\n"
               f"⚠️ The card will be disabled immediately.\n\n"
               f"Type **\"confirm\"** to proceed or **\"cancel\"** to exit.")
        return msg, {"step": 3, "data": {**data, "selected_card": selected}}

    # ── Step 3: Waiting for confirmation ─────────────────────────────────────
    if step == 3:
        if not _is_confirm(message):
            msg = ("請輸入「確認」執行掛失，或「取消」結束。"
                   if language == "zh" else "Type \"confirm\" to block the card or \"cancel\" to exit.")
            return msg, workflow

        selected = data["selected_card"]
        block_result = block_card(user_id, selected["card_id"])
        if not block_result.get("success"):
            msg = ("系統無法處理，請撥 0800-XXX-XXX 緊急掛失。"
                   if language == "zh" else "System error. Please call 0800-XXX-XXX immediately.")
            return msg, {"step": 0, "data": {}}

        ticket = create_ticket(
            type="card_loss",
            user_id=user_id,
            card_id=selected["card_id"],
            description=f"信用卡掛失：{selected['type']}（末碼 {selected['last4']}）",
            priority="high",
        )
        blocked_at = block_result["blocked_at"][:19].replace("T", " ")

        msg = (f"✅ 掛失完成！\n\n"
               f"**卡片**：{selected['type']}（末碼 {selected['last4']}）\n"
               f"**掛失時間**：{blocked_at}\n"
               f"**服務單號**：`{ticket['ticket_id']}`\n\n"
               f"客服將於 1 個工作日內聯繫您辦理補發，如需加急請撥 0800-XXX-XXX。\n\n"
               f"還有其他需要幫忙的嗎？"
               if language == "zh"
               else f"✅ Card successfully blocked!\n\n"
               f"**Card**: {selected['type']} (last 4: {selected['last4']})\n"
               f"**Blocked at**: {blocked_at}\n"
               f"**Ticket ID**: `{ticket['ticket_id']}`\n\n"
               f"Our team will contact you within 1 business day for card replacement.\n\n"
               f"Is there anything else I can help you with?")
        return msg, {"step": 0, "data": {}}

    return "發生錯誤，請重新嘗試。", {"step": 0, "data": {}}
