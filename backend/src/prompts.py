"""
System prompt construction + static response templates.
Moved out of main.py in Sprint 6 so the FAQ/Account Node can build the
same prompt the Sprint 1-5 if/else branch used, unchanged.
"""

from pathlib import Path
from typing import Optional

from .mock_api.mock_data import get_user_by_id

PROJECT_ROOT = Path(__file__).parent.parent.parent
KB_DIR = PROJECT_ROOT / "data" / "knowledge_base"


def load_kb(language: str) -> str:
    lang_dir = KB_DIR / language
    if not lang_dir.exists():
        return ""
    return "\n\n".join(
        f"=== {f.stem} ===\n{f.read_text(encoding='utf-8')}"
        for f in sorted(lang_dir.glob("*.md"))
    )


KB = {"zh": load_kb("zh"), "en": load_kb("en")}

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
