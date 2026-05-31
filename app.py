import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="TechBot Fuso",
    page_icon="🔧",
    layout="wide"
)


@st.cache_resource
def load_retriever():
    from retriever import get_ensemble_retriever
    return get_ensemble_retriever()


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    # format: [{"role": "user"|"assistant", "content": str, "sources": list}]

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

st.title("🔧 TechBot Fuso")
st.caption("Asisten teknis KTB untuk teknisi bengkel resmi Fuso · Canter FE 74 HD · Fighter X FN61 FSL")
st.divider()

with st.sidebar:
    st.markdown("### 🔧 TechBot Fuso")
    st.divider()

    if st.button("🗑️ New Chat", use_container_width=True, type="secondary"):
        st.session_state.chat_history = []
        st.rerun()

    st.divider()
    st.markdown("**Pertanyaan Umum:**")

    SUGGESTED_QUESTIONS = [
        "Fighter overheat di tanjakan, radiator dan thermostat normal. Apa yang harus dicek?",
        "Canter bunyi ketukan saat cold start, hilang setelah warm-up. Perlu tindakan segera?",
        "Interval filter udara Fighter X FN61 FSL di area tambang?",
        "Fighter power loss 2 bulan, filter udara dan BBM primer sudah diganti. Apa selanjutnya?",
    ]

    for i, q in enumerate(SUGGESTED_QUESTIONS):
        if st.button(q, key=f"sq_{i}", use_container_width=True):
            st.session_state.pending_query = q
            st.rerun()

tab_chat, tab_monitor = st.tabs(["💬 Asisten Teknis", "📊 Monitoring"])

# ─── Tab Chat ─────────────────────────────────────────────────────────────────

with tab_chat:

    # 1. Render semua history (loop ini yang handle SEMUA pesan)
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources"):
                with st.expander("📎 Sumber dokumen"):
                    for s in msg["sources"]:
                        st.markdown(f"• {s}")

    # 2. Chat input — selalu tepat setelah history, sebelum apapun
    user_input = st.chat_input("Tanyakan masalah teknis kendaraan Fuso...")

    # 3. Resolve query
    query = st.session_state.pending_query or user_input
    if st.session_state.pending_query:
        st.session_state.pending_query = None

    # 4. Process — TIDAK ada st.chat_message() di sini
    if query:
        # Append user message
        st.session_state.chat_history.append({
            "role": "user",
            "content": query
        })

        # Process (spinner boleh)
        with st.spinner("Mencari di knowledge base..."):
            from llm import ask
            from retriever import format_sources
            from monitoring import log_query, init_db

            init_db()
            retriever = load_retriever()
            result = ask(
                query,
                retriever,
                st.session_state.chat_history[:-1]
            )
            formatted_sources = format_sources(result["sources"])
            log_query(query, result, formatted_sources)

        # Append assistant response
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": result["answer"],
            "sources": [] if result["is_fallback"] else formatted_sources
        })

        # Rerun — history loop di atas yang akan render semuanya
        st.rerun()

# ─── Tab Monitoring ───────────────────────────────────────────────────────────

with tab_monitor:
    from monitoring import get_recent_logs, get_stats, init_db
    import pandas as pd

    init_db()
    stats = get_stats()

    st.subheader("Ringkasan")

    row1 = st.columns(3)
    row2 = st.columns(3)

    row1[0].metric("Total Query", stats["query_count"])
    row1[1].metric("Avg Response Time", f"{stats['avg_response_time']}s")
    row1[2].metric("Total Tokens", f"{stats['total_tokens']:,}")
    row2[0].metric("Estimated Cost", f"${stats['total_cost_usd']:.6f}")
    row2[1].metric("Fallback Rate", f"{stats['fallback_rate']}%")
    row2[2].metric("Most Referenced", stats["most_referenced_source"])

    st.subheader("Query Terbaru")
    logs = get_recent_logs(10)
    if logs:
        df = pd.DataFrame(logs)
        df.columns = [
            "Waktu", "Query", "Response Time (s)",
            "Tokens", "Cost (USD)", "Fallback"
        ]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada query yang tercatat.")

    st.divider()
    col_refresh, col_clear = st.columns([1, 1])

    with col_refresh:
        if st.button("🔄 Refresh Stats", use_container_width=True):
            st.rerun()

    with col_clear:
        if st.button("🗑️ Clear Semua Logs", type="secondary", use_container_width=True):
            import sqlite3
            conn = sqlite3.connect("monitoring.db")
            conn.execute("DELETE FROM query_logs")
            conn.commit()
            conn.close()
            st.success("Logs berhasil dihapus.")
            st.rerun()
