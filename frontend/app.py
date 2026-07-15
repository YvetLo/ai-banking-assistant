"""
AI Banking Customer Assistant — Frontend (Streamlit)
Sprint 1: FAQ Chat Interface
"""

import uuid

import requests
import streamlit as st

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="XX Bank AI 客服",
    page_icon="🏦",
    layout="centered",
    initial_sidebar_state="expanded",
)

API_URL = "http://localhost:8000"

DISCLAIMER = {
    "zh": "本助理提供之資訊僅供參考，不構成財務建議。實際利率、費用以官網公告為準。",
    "en": "Information provided is for reference only and does not constitute financial advice. Rates subject to official announcements.",
}

WELCOME = {
    "zh": "您好！我是 XX 銀行 AI 客服助理。請問有什麼可以幫您？\n\n我可以協助您查詢信用卡費用、帳戶服務、轉帳規則、ATM 服務等資訊。",
    "en": "Hello! I'm the XX Bank AI Customer Assistant. How can I help you today?\n\nI can assist with credit card fees, account services, transfer rules, ATM info, and more.",
}

# ── Session State ─────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "language" not in st.session_state:
    st.session_state.language = "zh"
if "welcomed" not in st.session_state:
    st.session_state.welcomed = False

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🏦 XX Bank AI 客服助理")
st.caption("Sprint 1 — FAQ Mode (Context Stuffing)")

lang = st.session_state.language
st.info(DISCLAIMER[lang])
st.divider()

# ── Welcome Message (first open) ──────────────────────────────────────────────
if not st.session_state.welcomed:
    with st.chat_message("assistant"):
        st.markdown(WELCOME[lang])
    st.session_state.welcomed = True

# ── Chat History ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Input ─────────────────────────────────────────────────────────────────────
user_input = st.chat_input("請輸入您的問題 / Ask your question...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    assistant_reply = ""
    with st.chat_message("assistant"):
        with st.spinner("思考中 / Thinking..."):
            try:
                resp = requests.post(
                    f"{API_URL}/chat",
                    json={
                        "message": user_input,
                        "session_id": st.session_state.session_id,
                        "history": st.session_state.messages,
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                assistant_reply = data["response"]
                st.session_state.language = data.get("language", "zh")

            except requests.exceptions.ConnectionError:
                assistant_reply = (
                    "⚠️ 無法連接到後端服務。\n\n"
                    "請在新的終端機執行：\n"
                    "```\nuvicorn backend.main:app --reload\n```"
                )
            except Exception as e:
                assistant_reply = f"⚠️ 發生錯誤：{e}"

        st.markdown(assistant_reply)

    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("系統資訊")
    st.write(f"**Sprint**: 1 — FAQ Mode")
    st.write(f"**Session**: `{st.session_state.session_id[:8]}...`")

    lang_label = "🇹🇼 繁體中文" if st.session_state.language == "zh" else "🇺🇸 English"
    st.write(f"**偵測語言**: {lang_label}")
    st.write(f"**對話輪數**: {len(st.session_state.messages) // 2} / 10")

    st.divider()

    if st.button("🗑️ 清除對話 / Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.welcomed = False
        st.rerun()

    st.divider()
    st.markdown("**💡 試試看 / Try asking:**")
    questions = [
        "信用卡年費多少？",
        "ATM 每天可以提多少錢？",
        "轉帳手續費怎麼算？",
        "網路銀行忘記密碼怎麼辦？",
        "What are the credit card cashback rates?",
        "What is the daily ATM withdrawal limit?",
    ]
    for q in questions:
        st.caption(f"• {q}")

    st.divider()
    st.caption("📞 客服專線：0800-XXX-XXX")
    st.caption("🕐 Mon–Fri 08:00–22:00")
