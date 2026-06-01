import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ─── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="TechBot Fuso",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────

st.markdown("""
<style>

/* 1. Hide Streamlit chrome */
#MainMenu                    { visibility: hidden; }
[data-testid="stHeader"]     { display: none !important; }
[data-testid="stToolbar"]    { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
footer                       { visibility: hidden; }
.block-container {
    padding-top: 0.75rem !important;
    padding-bottom: 1rem !important;
    max-width: 100% !important;
}

/* 2. Background & sidebar */

[data-testid="stSidebar"] {
    background-color: #F0F2F6 !important;
    border-right: 1px solid #E2E8F0 !important;
}

/* 3. Primary button — New Chat */
[data-testid="stSidebar"] [data-testid="baseButton-primary"] {
    background-color: #C0392B !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] [data-testid="baseButton-primary"]:hover {
    background-color: #A93226 !important;
}

/* 4. Secondary buttons — quick questions */
[data-testid="stSidebar"] [data-testid="baseButton-secondary"] {
    text-align: left !important;
    white-space: normal !important;
    height: auto !important;
    min-height: 0 !important;
    line-height: 1.4 !important;
    font-size: 11px !important;
    padding: 7px 9px !important;
    background-color: #F8FAFC !important;
    border: 1px solid #E2E8F0 !important;
    color: #334155 !important;
    border-radius: 8px !important;
    font-weight: 400 !important;
}
[data-testid="stSidebar"] [data-testid="baseButton-secondary"]:hover {
    background-color: #EFF6FF !important;
    border-color: #BFDBFE !important;
    color: #1D4ED8 !important;
}

/* 5. Tabs container */
.stTabs [data-baseweb="tab-list"] {
    background-color: #FFFFFF !important;
    border-bottom: 2px solid #E2E8F0 !important;
    padding: 0 8px !important;
    gap: 0 !important;
    border-radius: 8px 8px 0 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: #C0392B !important;
    height: 2px !important;
}
.stTabs [data-baseweb="tab-border"] { display: none !important; }
.stTabs [data-baseweb="tab"] {
    padding: 10px 20px !important;
    letter-spacing: 0.01em !important;
    margin-right: 8px !important;
}


</style>
""", unsafe_allow_html=True)


# ─── Cache & Session State ────────────────────────────────────────────────────

@st.cache_resource
def load_retriever():
    from retriever import get_ensemble_retriever
    return get_ensemble_retriever()


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    # format: [{"role": "user"|"assistant", "content": str, "sources": list}]

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None


# ─── Constants ────────────────────────────────────────────────────────────────

# (tag, question) — tag menentukan warna label kategori di sidebar
SUGGESTED_QUESTIONS = [
    ("troubleshoot", "Fighter overheat di tanjakan, radiator dan thermostat normal. Apa yang harus dicek?"),
    ("troubleshoot", "Fighter power loss 2 bulan, filter udara dan BBM primer sudah diganti. Apa selanjutnya?"),
    ("diagnosis",    "Canter bunyi ketukan saat cold start, hilang setelah warm-up. Perlu tindakan segera?"),
    ("maintenance",  "Interval filter udara Fighter X FN61 FSL di area tambang?"),
]

TAG_STYLES = {
    "troubleshoot": "background:#FEE2E2; color:#B91C1C;",
    "diagnosis":    "background:#FEF3C7; color:#B45309;",
    "maintenance":  "background:#D1FAE5; color:#065F46;",
}

# Ganti dengan jumlah dokumen aktual dari knowledge base sebelum demo
KNOWLEDGE_STATS = {
    "SOP":         2,
    "Field Cases": 9,
    "TSB":         2,
}
COVERAGE = ["Canter FE74 HD", "Fighter FN61 FSL"]


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:

    # 1. Logo
    st.image("fuso_logo.png", use_container_width=True)

    # 2. Title — plain markdown, no colored background
    st.markdown("### 🔧 TechBot Fuso")
    st.caption("Fuso Technical Knowledge Assistant")

    # 3. Status chips
    # @keyframes disertakan di dalam st.html() karena st.html() berjalan di
    # scope terisolasi dan tidak mewarisi CSS global dari st.markdown().
    st.html("""
    <style>
    @keyframes sPulse { 0%,100% { opacity:1; } 50% { opacity:0.3; } }
    </style>
    <div style="display:flex; gap:6px; flex-wrap:wrap; margin:2px 0 6px;">
        <span style="
            background:#F1F5F9; border:1px solid #E2E8F0; color:#64748B;
            padding:2px 8px; border-radius:20px; font-size:10px;
        ">Gemini 2.5 Flash Lite</span>
        <span style="
            background:rgba(93,202,165,0.12); border:1px solid #5DCAA5;
            color:#5DCAA5; padding:2px 8px; border-radius:20px;
            font-size:10px; font-weight:500;
            display:inline-flex; align-items:center; gap:3px;
        ">
            <span style="
                width:5px; height:5px; background:#5DCAA5; border-radius:50%;
                display:inline-block; animation:sPulse 2s infinite;
            "></span>
            live demo
        </span>
    </div>
    """)

    # 4. Tagline
    st.caption(
        "*Preserve · Distribute · Standardize* Technical knowledge "
        "across KTB service network"
    )

    st.divider()

    # 5. New Chat button
    if st.button("✏️ New Chat", use_container_width=True, type="primary", key="new_chat"):
        st.session_state.chat_history = []
        st.rerun()

    st.divider()

    # 6. Quick questions — grouped by category tag
    st.caption("CONTOH PERTANYAAN")

    last_tag = None
    for i, (tag, question) in enumerate(SUGGESTED_QUESTIONS):
        if tag != last_tag:
            tag_style = TAG_STYLES[tag]
            tag_name  = tag.upper()
            st.html(
                f'<div style="margin-top:6px; margin-bottom:2px;">'
                f'<span style="{tag_style} font-size:9px; font-weight:700; '
                f'padding:1px 6px; border-radius:3px; text-transform:uppercase; '
                f'letter-spacing:0.03em; display:inline-block;">{tag_name}</span>'
                f'</div>'
            )
            last_tag = tag
        if st.button(question, key=f"sq_{i}", use_container_width=True):
            st.session_state.pending_query = question
            st.rerun()

    st.divider()

    # 7. Knowledge sources & coverage — plain st.markdown() only, no HTML
    sop_count   = KNOWLEDGE_STATS["SOP"]
    cases_count = KNOWLEDGE_STATS["Field Cases"]
    tsb_count   = KNOWLEDGE_STATS["TSB"]
    coverage_str = " · ".join(COVERAGE)

    st.markdown(
        f"📚 **Knowledge Sources**  \n"
        f"📋 {sop_count} SOP   📁 {cases_count} Field Cases   📘 {tsb_count} TSB"
    )
    st.markdown(f"🗺️ **Coverage**  \n{coverage_str}")


# ─── Helper: Styled Source Cards ─────────────────────────────────────────────

def render_source_section(sources: list) -> None:
    """Source display pakai st.expander — collapsible, tidak perlu HTML."""
    if not sources:
        return

    TYPE_MAP = {
        "case":            ("📋", "Kasus lapangan"),
        "sop":             ("📗", "SOP resmi · KTB"),
        "tsb":             ("📘", "TSB resmi · Mitsubishi Fuso"),
        "troubleshooting": ("📘", "TSB resmi · Mitsubishi Fuso"),
    }

    with st.expander("📎 Sumber dokumen", expanded=False):
        for source in sources:
            icon, label = "📄", "Dokumen internal"
            for kw, (i, lbl) in TYPE_MAP.items():
                if kw in source.lower():
                    icon, label = i, lbl
                    break
            st.markdown(f"{icon} **{source}**")
            st.caption(label)


# ─── Tabs ─────────────────────────────────────────────────────────────────────

tab_chat, tab_monitor = st.tabs(["💬 Asisten Teknis", "📊 Monitoring"])


# ─── Tab: Asisten Teknis ──────────────────────────────────────────────────────

with tab_chat:

    # 1. Render chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources"):
                render_source_section(msg["sources"])

    # 2. Chat input — setelah history agar Streamlit pin ke bawah viewport
    user_input = st.chat_input("Tanyakan masalah teknis kendaraan Fuso...")

    # 3. Resolve query dari pending (sidebar button) atau chat input
    query = st.session_state.pending_query or user_input
    if st.session_state.pending_query:
        st.session_state.pending_query = None

    # 4. Process
    if query:
        st.session_state.chat_history.append({
            "role": "user",
            "content": query,
        })

        with st.spinner("Mencari di knowledge base..."):
            from llm import ask
            from retriever import format_sources
            from monitoring import init_db, log_query

            init_db()
            retriever = load_retriever()
            result = ask(
                query,
                retriever,
                st.session_state.chat_history[:-1],
            )
            formatted_sources = format_sources(result["sources"])
            log_query(query, result, formatted_sources)

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": result["answer"],
            "sources": [] if result["is_fallback"] else formatted_sources,
        })

        st.rerun()


# ─── Tab: Monitoring ──────────────────────────────────────────────────────────

with tab_monitor:
    from monitoring import get_recent_logs, get_stats, init_db
    import pandas as pd
    import plotly.graph_objects as go
    from datetime import date, timedelta

    init_db()
    stats    = get_stats()
    logs_100 = get_recent_logs(100)

    # ── 1. Section title ─────────────────────────────────────────────────────
    st.markdown("### Ringkasan sistem")

    # ── 2. KPI Cards ─────────────────────────────────────────────────────────

    def _card(label, value, sub, accent, value_size="22px", value_color="#1E293B", extra=""):
        return (
            f'<div style="background:white;border:0.5px solid #E2E8F0;'
            f'border-left:3px solid {accent};border-radius:0;padding:12px;font-family:sans-serif;">'
            f'<div style="font-size:9px;text-transform:uppercase;color:#64748B;'
            f'letter-spacing:0.05em;margin-bottom:4px;">{label}</div>'
            f'<div style="font-size:{value_size};font-weight:500;color:{value_color};">{value}</div>'
            f'<div style="font-size:10px;color:#64748B;margin-top:3px;">{sub}</div>'
            f'{extra}</div>'
        )

    today_str = date.today().isoformat()
    today_n   = sum(1 for r in logs_100 if r["timestamp"][:10] == today_str)
    today_sub = f"↑ +{today_n} hari ini" if today_n > 0 else "belum ada query hari ini"

    rate           = stats["fallback_rate"]
    rate_val_color = "#854F0B" if rate > 20 else "#3B6D11"
    rate_sub_color = "#854F0B" if rate > 20 else "#3B6D11"
    rate_sub_text  = "⚠ perlu tambah dokumen" if rate > 20 else "✓ dalam batas normal"
    bar_color      = "#854F0B" if rate > 20 else "#1D9E75"
    rate_bar       = (
        f'<div style="height:3px;background:#F1F5F9;border-radius:2px;margin-top:5px;">'
        f'<div style="height:100%;width:{min(rate, 100):.1f}%;background:{bar_color};"></div>'
        f'</div>'
    )

    tokens_per_q = stats["total_tokens"] // max(stats["query_count"], 1)
    per_q_idr    = (stats["total_cost_usd"] / max(stats["query_count"], 1)) * 16000

    most_ref         = stats["most_referenced_source"]
    most_ref_display = (most_ref[:35] + "...") if len(most_ref) > 35 else most_ref

    row1 = st.columns(3)
    row2 = st.columns(3)

    with row1[0]:
        st.html(_card("TOTAL QUERY", stats["query_count"], today_sub, "#378ADD"))
    with row1[1]:
        st.html(_card("AVG RESPONSE", f"{stats['avg_response_time']}s",
                      "rata-rata waktu respons", "#1D9E75"))
    with row1[2]:
        st.html(_card(
            "FALLBACK RATE", f"{rate}%",
            f'<span style="color:{rate_sub_color}">{rate_sub_text}</span>',
            "#BA7517", value_color=rate_val_color, extra=rate_bar,
        ))

    with row2[0]:
        st.html(_card("TOTAL TOKENS", f"{stats['total_tokens']:,}",
                      f"≈ {tokens_per_q:,} / query", "#7F77DD"))
    with row2[1]:
        st.html(_card("EST. COST", f"${stats['total_cost_usd']:.4f}",
                      f"≈ Rp {per_q_idr:,.0f} / query", "#1D9E75"))
    with row2[2]:
        st.html(_card("MOST REFERENCED", most_ref_display,
                      "dokumen paling sering dikutip", "#D4537E", value_size="12px"))

    # ── 3. Line chart ─────────────────────────────────────────────────────────
    st.markdown("**Volume query (7 hari)**")
    st.caption("Tren penggunaan per hari")

    today  = date.today()
    last_7 = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    day_totals    = {d.isoformat(): 0 for d in last_7}
    day_fallbacks = {d.isoformat(): 0 for d in last_7}

    for r in logs_100:
        d = r["timestamp"][:10]
        if d in day_totals:
            day_totals[d] += 1
            if r["is_fallback"]:
                day_fallbacks[d] += 1

    if not logs_100:
        st.info("Belum cukup data untuk grafik trend.")
    else:
        chart_dates     = list(day_totals.keys())
        chart_totals    = list(day_totals.values())
        chart_fallbacks = list(day_fallbacks.values())

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=chart_dates, y=chart_totals, name="total",
            mode="lines+markers", line=dict(color="#378ADD", width=2),
        ))
        fig.add_trace(go.Scatter(
            x=chart_dates, y=chart_fallbacks, name="fallback",
            mode="lines", line=dict(color="#D85A30", width=1.5, dash="dash"),
        ))
        fig.update_layout(
            height=200, margin=dict(l=10, r=10, t=10, b=30),
            plot_bgcolor="white", paper_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1),
            xaxis=dict(showgrid=False, tickformat="%d/%m"),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── 4. Query log table ────────────────────────────────────────────────────
    col_title, col_search = st.columns([2, 1])
    col_title.markdown("**Log query terbaru**")
    search = col_search.text_input("", placeholder="Cari query...", label_visibility="collapsed")

    logs_10 = get_recent_logs(10)
    df = pd.DataFrame([
        {
            "Waktu":      r["timestamp"],
            "Query":      r["query"],
            "Resp (s)":   r["response_time"],
            "Tokens":     r["total_tokens"],
            "Cost (USD)": r["estimated_cost"],
            "Status":     "↩ fallback" if r["is_fallback"] else "✓ RAG",
        }
        for r in logs_10
    ])

    if search and not df.empty:
        df = df[df["Query"].str.contains(search, case=False, na=False)]

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Waktu":      st.column_config.TextColumn(width="small"),
            "Query":      st.column_config.TextColumn(width="large"),
            "Resp (s)":   st.column_config.NumberColumn(width="small", format="%.2f"),
            "Tokens":     st.column_config.NumberColumn(width="small"),
            "Cost (USD)": st.column_config.NumberColumn(width="small", format="$%.4f"),
            "Status":     st.column_config.TextColumn(width="small"),
        },
    )

    # ── 5. Action buttons ─────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    csv_data = df.to_csv(index=False).encode("utf-8")
    col1.download_button(
        "📥 Export CSV", csv_data,
        file_name="techbot_logs.csv", mime="text/csv",
        use_container_width=True,
    )

    if col2.button("🔄 Refresh Stats", use_container_width=True):
        st.rerun()

    if col3.button("🗑 Clear Semua Logs", use_container_width=True, type="secondary"):
        import sqlite3
        conn = sqlite3.connect("monitoring.db")
        conn.execute("DELETE FROM query_logs")
        conn.commit()
        conn.close()
        st.success("Logs berhasil dihapus.")
        st.rerun()
