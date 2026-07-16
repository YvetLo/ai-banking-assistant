"""
AI Banking Customer Assistant — Frontend (Streamlit)
Sprint 2: FAQ + Account Query with Login
"""

import uuid

import requests
import streamlit as st

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="XX Bank AI 客服",
    page_icon="🏦",
    layout="centered",
    initial_sidebar_state="expanded",
)

API_URL = "http://localhost:8000"

DISCLAIMER = {
    "zh": "本助理提供之資訊僅供參考，不構成財務建議。實際利率、費用以官網公告為準。",
    "en": "Information provided is for reference only and does not constitute financial advice.",
}

WELCOME = {
    "zh": "您好！我是 XX 銀行 AI 客服助理，可以協助您查詢信用卡費用、帳戶服務、轉帳規則等資訊。\n\n登入後還可以查詢您的個人帳單和消費明細喔！",
    "en": "Hello! I'm the XX Bank AI Assistant. I can help with credit cards, account services, transfers, and more.\n\nLog in to also check your personal bill and transaction history!",
}

TEST_ACCOUNTS = [
    ("demo_user1", "demo1234", "陳小明（一般上班族，2 張信用卡）"),
    ("demo_user2", "demo5678", "王大明（商務人士，無限卡）"),
    ("demo_user3", "demo9999", "陳春花（銀髮族，定存帳戶）"),
]

# ── Session State Init ─────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "session_id": str(uuid.uuid4()),
        "messages": [],
        "language": "zh",
        "welcomed": False,
        "user_id": None,
        "user_name": None,
        "is_authenticated": False,
        "workflow": {"step": 0, "data": {}},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ── Sidebar — Login ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🏦 XX Bank AI 客服")
    st.divider()

    if not st.session_state.is_authenticated:
        st.subheader("🔐 登入帳號")
        username = st.text_input("帳號 / Username", key="login_username")
        password = st.text_input("密碼 / Password", type="password", key="login_password")

        if st.button("登入 / Login", use_container_width=True, type="primary"):
            if username and password:
                try:
                    resp = requests.post(
                        f"{API_URL}/mock-api/auth/login",
                        json={"username": username, "password": password},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.user_id = data["user_id"]
                        st.session_state.user_name = data["name"]
                        st.session_state.is_authenticated = True
                        st.session_state.messages = []
                        st.session_state.welcomed = False
                        st.rerun()
                    else:
                        st.error("帳號或密碼錯誤")
                except requests.exceptions.ConnectionError:
                    st.error("無法連接後端，請確認 uvicorn 已啟動")
            else:
                st.warning("請輸入帳號和密碼")

        with st.expander("📋 測試帳號"):
            for uname, pwd, desc in TEST_ACCOUNTS:
                st.caption(f"**{uname}** / {pwd}")
                st.caption(f"  → {desc}")

    else:
        st.success(f"✅ 已登入")
        st.write(f"**{st.session_state.user_name}**")
        st.caption(f"ID: {st.session_state.user_id}")

        if st.button("登出 / Logout", use_container_width=True):
            st.session_state.is_authenticated = False
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.session_state.messages = []
            st.session_state.welcomed = False
            st.rerun()

    st.divider()
    st.write(f"**Sprint**: 3 — FAQ + Account + Card Loss")
    st.write(f"**Session**: `{st.session_state.session_id[:8]}...`")
    lang_label = "🇹🇼 繁體中文" if st.session_state.language == "zh" else "🇺🇸 English"
    st.write(f"**語言**: {lang_label}")
    st.write(f"**對話輪數**: {len(st.session_state.messages) // 2} / 10")

    st.divider()
    st.markdown("**💡 可以問：**")
    if st.session_state.is_authenticated:
        st.caption("• 我本月帳單多少？")
        st.caption("• 我的帳戶餘額是多少？")
        st.caption("• 幫我看最近的消費明細")
        st.caption("• 我要掛失信用卡")
        st.caption("• What's my current bill?")
    else:
        st.caption("• 信用卡年費多少？")
        st.caption("• ATM 每天可以提多少？")
        st.caption("• 轉帳手續費怎麼算？")
        st.caption("• What is the cashback rate?")

    st.divider()
    if st.button("🗑️ 清除對話", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.welcomed = False
        st.rerun()

# ── Main Chat Area ─────────────────────────────────────────────────────────────
st.title("🏦 XX Bank AI 客服助理")

lang = st.session_state.language
st.info(DISCLAIMER[lang])

if st.session_state.is_authenticated:
    st.caption(f"🔓 登入身分：{st.session_state.user_name}")

# Workflow progress banner
wf_step = st.session_state.workflow.get("step", 0)
if wf_step > 0:
    STEP_LABELS = {1: "步驟 1/3：身分驗證", 2: "步驟 2/3：選擇卡片", 3: "步驟 3/3：確認掛失"}
    st.warning(f"🔒 信用卡掛失流程進行中 — {STEP_LABELS.get(wf_step, '')}　　輸入「取消」可結束流程")

st.divider()

# Welcome message
if not st.session_state.welcomed:
    with st.chat_message("assistant"):
        st.markdown(WELCOME[lang])
    st.session_state.welcomed = True

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
user_input = st.chat_input("請輸入您的問題 / Ask your question...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    assistant_reply = ""
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                resp = requests.post(
                    f"{API_URL}/chat",
                    json={
                        "message": user_input,
                        "session_id": st.session_state.session_id,
                        "history": st.session_state.messages,
                        "user_id": st.session_state.user_id,
                        "workflow": st.session_state.workflow,
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                assistant_reply = data["response"]
                st.session_state.language = data.get("language", "zh")
                st.session_state.workflow = data.get("workflow", {"step": 0, "data": {}})

            except requests.exceptions.ConnectionError:
                assistant_reply = (
                    "⚠️ 無法連接後端。請執行：\n```\nuvicorn backend.main:app --reload\n```"
                )
            except Exception as e:
                assistant_reply = f"⚠️ 錯誤：{e}"

        st.markdown(assistant_reply)

    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
