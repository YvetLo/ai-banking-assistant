"""
AI Banking Customer Assistant — Dashboard (Streamlit Page)
Sprint 4: Unresolved queries stats + ticket overview
"""

import requests
import streamlit as st

st.set_page_config(
    page_title="後台 Dashboard — XX Bank AI 客服",
    page_icon="📊",
    layout="wide",
)

API_URL = "http://localhost:8000"

st.title("📊 AI 客服後台 Dashboard")
st.caption("Sprint 4 — 未解決查詢統計 & 服務單管理")
st.divider()


def fetch(endpoint: str, params: dict = None):
    try:
        r = requests.get(f"{API_URL}{endpoint}", params=params, timeout=10)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "⚠️ 無法連接後端，請確認 uvicorn 已啟動"
    except Exception as e:
        return None, f"⚠️ 錯誤：{e}"


# ── Metrics Row ───────────────────────────────────────────────────────────────
stats, err = fetch("/stats")

if err:
    st.error(err)
else:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📋 服務單總數", stats["total_tickets"])
    col2.metric("🔴 待處理服務單", stats["open_tickets"])
    col3.metric("❓ 未解決查詢", stats["total_unresolved"])
    resolved_pct = (
        round(
            (stats["total_tickets"] / max(stats["total_unresolved"] + stats["total_tickets"], 1)) * 100
        )
        if stats["total_unresolved"] + stats["total_tickets"] > 0
        else 0
    )
    col4.metric("✅ 服務單轉換率", f"{resolved_pct}%", help="服務單數 / (未解決 + 服務單)")

    st.divider()

    # ── Unresolved by Reason Chart ────────────────────────────────────────────
    st.subheader("未解決查詢 — 觸發原因分析")
    by_reason = stats.get("unresolved_by_reason", {})

    if by_reason:
        LABELS = {
            "negative_feedback": "😤 否定回饋",
            "handoff_intent": "🤝 要求真人",
            "fallback_threshold": "🔁 連續未解決（≥3）",
        }
        chart_data = {LABELS.get(k, k): v for k, v in by_reason.items()}
        st.bar_chart(chart_data)
    else:
        st.info("目前沒有未解決查詢記錄。")

st.divider()

# ── Recent Unresolved Queries Table ──────────────────────────────────────────
st.subheader("最近未解決查詢")

unresolved, err2 = fetch("/unresolved", {"limit": 20})
if err2:
    st.error(err2)
elif not unresolved:
    st.success("🎉 目前沒有未解決查詢！")
else:
    REASON_LABEL = {
        "negative_feedback": "😤 否定回饋",
        "handoff_intent": "🤝 要求真人",
        "fallback_threshold": "🔁 連續未解決",
    }
    rows = [
        {
            "時間": r["created_at"][:19].replace("T", " "),
            "用戶問題": r["user_query"],
            "語言": "🇹🇼 中文" if r["language"] == "zh" else "🇺🇸 英文",
            "觸發原因": REASON_LABEL.get(r["trigger_reason"], r["trigger_reason"]),
            "意圖": r.get("intent", "—"),
            "Session": r["session_id"][:8] + "..." if r.get("session_id") else "—",
        }
        for r in unresolved
    ]
    st.dataframe(rows, use_container_width=True)

st.divider()

# ── Recent Tickets Table ──────────────────────────────────────────────────────
st.subheader("最近服務單")

tickets, err3 = fetch("/tickets", {"limit": 20})
if err3:
    st.error(err3)
elif not tickets:
    st.info("目前沒有服務單。")
else:
    STATUS_LABEL = {"open": "🔴 待處理", "closed": "✅ 已結案", "in_progress": "🟡 處理中"}
    rows = [
        {
            "服務單號": t["id"],
            "建立時間": t["created_at"][:19].replace("T", " "),
            "類型": t["type"],
            "說明": t.get("description", "—"),
            "優先度": t.get("priority", "normal"),
            "狀態": STATUS_LABEL.get(t["status"], t["status"]),
            "用戶": t.get("user_id", "—"),
        }
        for t in tickets
    ]
    st.dataframe(rows, use_container_width=True)

# ── Knowledge Base Gap Hint ───────────────────────────────────────────────────
st.divider()
with st.expander("💡 知識庫優化流程提示"):
    st.markdown("""
**未解決問題 → 知識庫補強步驟：**

1. 查看上方「未解決查詢」，找出高頻或重複的問題
2. 判斷是知識庫缺漏（需補充 FAQ 文件）還是範圍外問題（需更新安全守衛規則）
3. 在 `data/knowledge_base/zh/` 或 `en/` 新增或修改 `.md` 文件
4. Sprint 5 完成後執行 `python scripts/build_index.py` 重建向量索引
5. 重新測試原本 Fallback 的問題，確認解決率提升
""")
