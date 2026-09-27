"""
VAULT — AI Expense Agent
A mission-console redesign: dark instrument panel, one hero number,
one agent console. Category ledger stays quiet and data-driven.
"""

import streamlit as st
import pandas as pd

from llm_categorize import categorize_batch
from qa_agent import ask_agent
from db import (
    create_table,
    insert_transactions_bulk,
    get_all_transactions,
    get_spending_by_category,
    clear_table,
)

st.set_page_config(page_title="VAULT — AI Expense Agent", page_icon="◆", layout="wide")

CATEGORY_COLORS = {
    "Food": "#FF6B6B",
    "Transport": "#6C8CFF",
    "Bills": "#FFB454",
    "Shopping": "#00D9A3",
    "Entertainment": "#C792EA",
    "Other": "#7C8A9A",
}

# ---------- Global styling ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0E1420; }

    h1, h2, h3 { font-family: 'Sora', sans-serif !important; color: #EDF2F4; }
    p, span, label, div { color: #EDF2F4; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0A0F18;
        border-right: 1px solid #1E2636;
    }
    .brand {
        font-family: 'Sora', sans-serif;
        font-weight: 700;
        font-size: 1.4rem;
        letter-spacing: 0.02em;
        color: #EDF2F4;
        padding: 0.4rem 0 0.1rem 0;
    }
    .brand span { color: #00D9A3; }
    .brand-sub {
        font-size: 0.78rem;
        color: #7C8A9A;
        margin-bottom: 1.6rem;
    }
    .sidebar-label {
        font-family: 'Sora', sans-serif;
        font-size: 0.85rem;
        font-weight: 600;
        color: #7C8A9A;
        margin-top: 1.2rem;
        margin-bottom: 0.4rem;
    }

    /* Hero panel */
    .hero {
        background: linear-gradient(150deg, #161D2C 0%, #121826 100%);
        border: 1px solid #232C40;
        border-radius: 14px;
        padding: 2rem 2.2rem;
        margin-bottom: 1.6rem;
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: "";
        position: absolute;
        top: -40%; right: -10%;
        width: 260px; height: 260px;
        background: radial-gradient(circle, rgba(0,217,163,0.12) 0%, transparent 70%);
    }
    .hero-label {
        font-size: 0.85rem;
        color: #7C8A9A;
        font-weight: 500;
        margin-bottom: 0.3rem;
    }
    .hero-number {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 3.1rem;
        color: #EDF2F4;
        letter-spacing: -0.01em;
        line-height: 1.1;
    }
    .hero-number span { color: #00D9A3; }
    .hero-meta {
        font-size: 0.85rem;
        color: #7C8A9A;
        margin-top: 0.5rem;
    }

    /* Stat row */
    .stat-block {
        border-top: 2px solid #232C40;
        padding-top: 0.5rem;
    }
    .stat-num {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 1.5rem;
        color: #EDF2F4;
    }
    .stat-label {
        font-size: 0.8rem;
        color: #7C8A9A;
    }

    /* Ledger (category breakdown) */
    .ledger-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.55rem 0;
        border-bottom: 1px solid #1B2333;
    }
    .ledger-left { display: flex; align-items: center; gap: 0.6rem; }
    .ledger-dot { width: 8px; height: 8px; border-radius: 2px; }
    .ledger-name { font-size: 0.92rem; color: #EDF2F4; font-weight: 500; }
    .ledger-amt { font-family: 'JetBrains Mono', monospace; font-size: 0.92rem; color: #EDF2F4; font-weight: 500; }
    .ledger-track { background: #1B2333; height: 4px; border-radius: 2px; margin-top: 0.45rem; }
    .ledger-fill { height: 4px; border-radius: 2px; }

    /* Agent console */
    .console {
        background: #10161F;
        border: 1px solid #232C40;
        border-left: 3px solid #6C8CFF;
        border-radius: 10px;
        padding: 1.3rem 1.5rem;
        margin-top: 0.5rem;
    }
    .console-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #6C8CFF;
        margin-bottom: 0.5rem;
        letter-spacing: 0.03em;
    }
    .console-q {
        font-family: 'Sora', sans-serif;
        font-size: 1.02rem;
        font-weight: 600;
        color: #EDF2F4;
        margin-bottom: 0.6rem;
    }
    .console-a {
        font-size: 0.96rem;
        color: #C7D0D9;
        line-height: 1.55;
    }

    div[data-testid="stTextInput"] input {
        background-color: #10161F;
        border: 1px solid #232C40;
        color: #EDF2F4;
        border-radius: 8px;
        font-family: 'Inter', sans-serif;
    }
    div[data-testid="stTextInput"] input::placeholder { color: #55606F; }

    div[data-testid="stFileUploader"] section {
        background-color: #10161F;
        border: 1px dashed #2A3448;
        border-radius: 8px;
    }

    .stDataFrame { border: 1px solid #232C40 !important; border-radius: 8px; }

    .page-header {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        margin-bottom: 1.4rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #1E2636;
    }
    .page-title {
        font-family: 'Sora', sans-serif;
        font-weight: 700;
        font-size: 1.6rem;
        color: #EDF2F4;
        letter-spacing: -0.01em;
    }
    .page-title span { color: #00D9A3; }
    .page-tagline {
        font-size: 0.85rem;
        color: #7C8A9A;
    }

    hr { border-color: #1E2636; }
</style>
""", unsafe_allow_html=True)

create_table()

st.markdown("""
<div class="page-header">
    <div>
        <div class="page-title">VAULT<span>.</span></div>
    </div>
    <div class="page-tagline">AI-native spend intelligence</div>
</div>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown('<div class="brand">VAULT<span>.</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">AI-native spend intelligence</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">DATA SOURCE</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Transactions CSV", type=["csv"], label_visibility="collapsed")
    st.caption("Columns required: date, merchant, amount")

    st.markdown('<div class="sidebar-label">ASK THE AGENT</div>', unsafe_allow_html=True)
    st.caption("What did I spend the most on?")
    st.caption("How much on Food this month?")
    st.caption("What were my top 3 expenses?")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    required_cols = {"date", "merchant", "amount"}

    if not required_cols.issubset(set(df.columns)):
        st.error(f"CSV must have these columns: {required_cols}")
    else:
        if st.session_state.get("last_file") != uploaded_file.name:
            st.session_state.last_file = uploaded_file.name
            st.session_state.chat_history = []
            clear_table()
            with st.spinner("Categorizing transactions..."):
                merchant_list = df["merchant"].tolist()
                category_map = categorize_batch(merchant_list)
                rows_to_insert = [
                    (row["date"], row["merchant"], row["amount"], category_map.get(row["merchant"], "Other"))
                    for _, row in df.iterrows()
                ]
                insert_transactions_bulk(rows_to_insert)

        all_txns = get_all_transactions()
        category_data = get_spending_by_category()
        total_spent = sum(r[2] for r in all_txns)
        top_category = category_data[0][0] if category_data else "N/A"
        max_cat_amount = max((c[1] for c in category_data), default=1)
        date_range = f"{min(r[0] for r in all_txns)} to {max(r[0] for r in all_txns)}" if all_txns else ""

        # ---------- Hero ----------
        st.markdown(f"""
        <div class="hero">
            <div class="hero-label">Total spend</div>
            <div class="hero-number"><span>₹</span>{total_spent:,.0f}</div>
            <div class="hero-meta">{len(all_txns)} transactions · {date_range}</div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="stat-block"><div class="stat-num">{len(all_txns)}</div><div class="stat-label">Transactions</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="stat-block"><div class="stat-num">{top_category}</div><div class="stat-label">Top category</div></div>', unsafe_allow_html=True)
        with c3:
            avg = total_spent / len(all_txns) if all_txns else 0
            st.markdown(f'<div class="stat-block"><div class="stat-num">₹{avg:,.0f}</div><div class="stat-label">Avg. transaction</div></div>', unsafe_allow_html=True)

        st.write("")
        left, right = st.columns([1, 1.1], gap="large")

        with left:
            st.markdown("##### Category breakdown")
            for cat, amt in category_data:
                pct = (amt / max_cat_amount) * 100 if max_cat_amount else 0
                color = CATEGORY_COLORS.get(cat, "#7C8A9A")
                st.markdown(f"""
                <div class="ledger-row" style="display:block;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div class="ledger-left">
                            <div class="ledger-dot" style="background:{color};"></div>
                            <div class="ledger-name">{cat}</div>
                        </div>
                        <div class="ledger-amt">₹{amt:,.0f}</div>
                    </div>
                    <div class="ledger-track"><div class="ledger-fill" style="width:{pct}%; background:{color};"></div></div>
                </div>
                """, unsafe_allow_html=True)

        with right:
            st.markdown("##### Ledger")
            display_df = pd.DataFrame(all_txns, columns=["Date", "Merchant", "Amount", "Category"])
            st.dataframe(display_df, width="stretch", height=310)

        st.write("")
        st.markdown("##### Agent console")
        question = st.text_input("ask", placeholder="Ask the agent about your spending...", label_visibility="collapsed")

        if question:
            with st.spinner("Agent is thinking..."):
                result = ask_agent(question)
            st.session_state.chat_history.insert(0, {"q": question, "result": result})

        if st.session_state.chat_history:
            latest = st.session_state.chat_history[0]
            st.markdown(f"""
            <div class="console">
                <div class="console-tag">AGENT RESPONSE</div>
                <div class="console-q">{latest['q']}</div>
                <div class="console-a">{latest['result']['answer']}</div>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("View generated SQL"):
                st.code(latest["result"]["sql"], language="sql")
                if "rows" in latest["result"]:
                    st.write("Raw data returned:", latest["result"]["rows"])
                if "error" in latest["result"]:
                    st.error(f"Debug info: {latest['result']['error']}")

        if len(st.session_state.chat_history) > 1:
            with st.expander(f"Question history ({len(st.session_state.chat_history) - 1} earlier)"):
                for item in st.session_state.chat_history[1:]:
                    st.markdown(f"**{item['q']}**")
                    st.markdown(f'<div class="console-a">{item["result"]["answer"]}</div>', unsafe_allow_html=True)
                    st.code(item["result"]["sql"], language="sql")
                    st.divider()
else:
    st.markdown("""
    <div class="hero">
        <div class="hero-label">Get started</div>
        <div style="font-family:'Sora',sans-serif; font-size:1.3rem; font-weight:600; margin-top:0.3rem;">
            Upload a transactions CSV from the sidebar
        </div>
        <div class="hero-meta">Columns required: date, merchant, amount</div>
    </div>
    """, unsafe_allow_html=True)