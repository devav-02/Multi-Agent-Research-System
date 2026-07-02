"""
ResearchMind — Streamlit UI for the Multi-Agent Research System.

Run with:
    streamlit run app.py

This file sits alongside pipeline.py, agents.py, and tools.py and provides
a landing-page-style UI on top of `run_research_pipeline`. No changes to
the pipeline logic are required — this reads its stdout to animate the
pipeline status cards live.
"""

import io # This is for import the files
import re
import contextlib
from datetime import datetime

import streamlit as st

from pipeline import run_research_pipeline


# --------------------------------------------------------------------------
# Page config
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="ResearchMind — AI Research",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------------------------------
# Global styling
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        .stApp {
            background: #08080a;
            background-image:
                radial-gradient(circle at 15% -10%, rgba(251,146,60,0.10), transparent 45%),
                radial-gradient(circle at 100% 20%, rgba(251,146,60,0.06), transparent 40%);
            font-family: 'Inter', sans-serif;
        }

        .block-container {
            padding-top: 3rem;
            padding-bottom: 3rem;
            max-width: 1280px;
        }

        /* ---------- Hero ---------- */
        .eyebrow {
            font-family: 'Space Grotesk', sans-serif;
            color: #fb923c;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.22em;
            text-transform: uppercase;
            margin-bottom: 1.1rem;
        }
        .hero-title {
            font-family: 'Archivo Black', sans-serif;
            font-weight: 400;
            font-size: clamp(2.6rem, 5.6vw, 4.6rem);
            line-height: 0.98;
            letter-spacing: -0.01em;
            color: #f5f5f4;
            margin: 0 0 1.3rem 0;
        }
        .hero-title .accent {
            color: #fb923c;
        }
        .hero-sub {
            color: #9ca3af;
            font-size: 1.02rem;
            max-width: 560px;
            line-height: 1.65;
            margin-bottom: 2.2rem;
        }

        /* ---------- Inputs & buttons ---------- */
        div[data-testid="stTextInput"] input {
            background: #101116 !important;
            border: 1px solid rgba(255,255,255,0.10) !important;
            border-radius: 14px !important;
            padding: 1.05rem 1.15rem !important;
            color: #e5e7eb !important;
            font-size: 0.98rem !important;
            font-family: 'Inter', sans-serif !important;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #fb923c !important;
            box-shadow: 0 0 0 3px rgba(251,146,60,0.15) !important;
        }
        div[data-testid="stTextInput"] input::placeholder {
            color: #6b7280 !important;
        }

        .stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #f97316, #fb923c) !important;
            border: none !important;
            border-radius: 14px !important;
            padding: 0.85rem 1.4rem !important;
            font-weight: 700 !important;
            font-size: 0.98rem !important;
            font-family: 'Space Grotesk', sans-serif !important;
            color: #0a0a0a !important;
            width: 100%;
            box-shadow: 0 10px 26px rgba(249,115,22,0.30);
            transition: filter 0.15s ease, transform 0.15s ease;
        }
        .stButton > button[kind="primary"]:hover {
            filter: brightness(1.08);
            transform: translateY(-1px);
        }

        .stButton > button[kind="secondary"] {
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid rgba(255,255,255,0.10) !important;
            border-radius: 999px !important;
            padding: 0.4rem 1.05rem !important;
            color: #d1d5db !important;
            font-size: 0.82rem !important;
            font-family: 'Inter', sans-serif !important;
        }
        .stButton > button[kind="secondary"]:hover {
            border-color: #fb923c !important;
            color: #fb923c !important;
        }

        .try-label {
            font-family: 'Space Grotesk', sans-serif;
            color: #6b7280;
            font-size: 0.78rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin: 1.5rem 0 0.7rem 0;
        }

        /* ---------- Pipeline panel ---------- */
        .pipeline-heading {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 700;
            font-size: 1.4rem;
            color: #f5f5f4;
            margin-bottom: 1.1rem;
        }
        .pipeline-card {
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.08);
            background: rgba(255,255,255,0.025);
            padding: 1.1rem 1.3rem;
            margin-bottom: 0.85rem;
            transition: border-color 0.2s ease, background 0.2s ease;
        }
        .pc-num {
            font-family: 'Space Grotesk', sans-serif;
            color: #fb923c;
            font-weight: 700;
            font-size: 0.82rem;
        }
        .pc-title {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 700;
            font-size: 1.02rem;
            color: #f5f5f4;
            margin-top: 0.15rem;
        }
        .pc-desc {
            color: #8b8f98;
            font-size: 0.83rem;
            margin-top: 0.15rem;
        }
        .pc-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.66rem;
            font-weight: 500;
            letter-spacing: 0.08em;
            padding: 3px 10px;
            border-radius: 999px;
            white-space: nowrap;
        }
        @keyframes pulse {
            0%   { opacity: 1; }
            50%  { opacity: 0.45; }
            100% { opacity: 1; }
        }
        .pc-running { animation: pulse 1.4s ease-in-out infinite; }

        /* ---------- Results ---------- */
        .results-heading {
            font-family: 'Space Grotesk', sans-serif;
            color: #f5f5f4;
            font-size: 1.3rem;
            font-weight: 700;
            margin: 2.6rem 0 1rem 0;
        }
        .results-heading .accent { color: #fb923c; }

        .report-card {
            padding: 1.7rem 1.9rem;
            border-radius: 16px;
            background: rgba(255,255,255,0.025);
            border: 1px solid rgba(255,255,255,0.08);
            color: #d1d5db;
            font-family: 'Inter', sans-serif;
            line-height: 1.65;
        }

        .log-box {
            background: #050506;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 1rem 1.1rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.76rem;
            color: #93c5fd;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
        }

        div[data-testid="stTabs"] button {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 600;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# Pipeline metadata + status card renderer
# --------------------------------------------------------------------------
PIPELINE_STEPS = {
    1: ("Search Agent", "Gathers recent web information"),
    2: ("Reader Agent", "Scrapes & extracts deep content"),
    3: ("Writer Chain", "Drafts the full research report"),
    4: ("Critic Chain", "Reviews & scores the report"),
}

STATUS_STYLES = {
    "WAITING": ("#6b7280", "rgba(255,255,255,0.05)", ""),
    "RUNNING": ("#fb923c", "rgba(251,146,60,0.14)", "pc-running"),
    "DONE":    ("#22c55e", "rgba(34,197,94,0.14)", ""),
}

STEP_MARKERS = {
    "step 1": 1,
    "step 2": 2,
    "step 3": 3,
    "step 4": 4,
}


def render_card(placeholder, num, title, desc, status):
    color, bg, anim_class = STATUS_STYLES[status]
    placeholder.markdown(
        f"""
        <div class="pipeline-card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.6rem;">
                <div>
                    <div class="pc-num">{num:02d}</div>
                    <div class="pc-title">{title}</div>
                    <div class="pc-desc">{desc}</div>
                </div>
                <span class="pc-badge {anim_class}" style="color:{color};background:{bg};">{status}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


class StreamlitLogWriter(io.StringIO):
    """Redirects pipeline.py's print() output into the UI, and parses it
    to advance the pipeline status cards live."""

    def __init__(self, log_placeholder, card_placeholders):
        super().__init__()
        self.log_placeholder = log_placeholder
        self.card_placeholders = card_placeholders
        self.buffer = ""
        self.triggered = set()

    def write(self, s):
        self.buffer += s
        low = self.buffer.lower()

        for marker, step_num in STEP_MARKERS.items():
            if marker in low and step_num not in self.triggered:
                self.triggered.add(step_num)
                if step_num > 1:
                    prev_title, prev_desc = PIPELINE_STEPS[step_num - 1]
                    render_card(self.card_placeholders[step_num - 1], step_num - 1, prev_title, prev_desc, "DONE")
                cur_title, cur_desc = PIPELINE_STEPS[step_num]
                render_card(self.card_placeholders[step_num], step_num, cur_title, cur_desc, "RUNNING")

        if self.log_placeholder is not None:
            safe = re.sub(r"[<>]", lambda m: "&lt;" if m.group() == "<" else "&gt;", self.buffer[-4000:])
            self.log_placeholder.markdown(f'<div class="log-box">{safe}</div>', unsafe_allow_html=True)

        return len(s)

    def flush(self):
        pass


# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------
if "result" not in st.session_state:
    st.session_state.result = None
if "ran_topic" not in st.session_state:
    st.session_state.ran_topic = ""
if "topic_input" not in st.session_state:
    st.session_state.topic_input = ""


def set_topic(value):
    st.session_state.topic_input = value


# --------------------------------------------------------------------------
# Layout: Hero (left) + Pipeline panel (right)
# --------------------------------------------------------------------------
left, right = st.columns([1.55, 1], gap="large")

with left:
    st.markdown('<div class="eyebrow">Multi-Agent AI System</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="hero-title">Research<span class="accent">Mind</span></h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-sub">Four specialized AI agents collaborate — searching, scraping, '
        'writing, and critiquing — to deliver a polished research report on any topic.</p>',
        unsafe_allow_html=True,
    )

    st.text_input(
        "Research topic",
        key="topic_input",
        placeholder="e.g. Quantum computing breakthroughs in 2025",
        label_visibility="collapsed",
    )

    run_clicked = st.button("⚡ Run Research Pipeline", type="primary")

    st.markdown('<div class="try-label">Try →</div>', unsafe_allow_html=True)
    chip_cols = st.columns(3)
    suggestions = ["LLM agents 2025", "CRISPR gene editing", "Fusion energy progress"]
    for col, suggestion in zip(chip_cols, suggestions):
        with col:
            st.button(suggestion, key=f"chip_{suggestion}", on_click=set_topic, args=(suggestion,))

with right:
    st.markdown('<div class="pipeline-heading">Pipeline</div>', unsafe_allow_html=True)
    card_placeholders = {}
    for num, (title, desc) in PIPELINE_STEPS.items():
        card_placeholders[num] = st.empty()
        render_card(card_placeholders[num], num, title, desc, "WAITING")

log_expander = st.expander("🖥️ View live agent logs", expanded=False)
with log_expander:
    log_placeholder = st.empty()
    log_placeholder.markdown('<div class="log-box">Logs will appear here once the pipeline runs...</div>', unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Run pipeline
# --------------------------------------------------------------------------
if run_clicked:
    topic = st.session_state.topic_input.strip()
    if not topic:
        st.warning("Please enter a research topic first.")
    else:
        # reset cards to WAITING before starting a fresh run
        for num, (title, desc) in PIPELINE_STEPS.items():
            render_card(card_placeholders[num], num, title, desc, "WAITING")

        writer = StreamlitLogWriter(log_placeholder, card_placeholders)
        try:
            with st.spinner("Agents are working..."):
                with contextlib.redirect_stdout(writer):
                    result = run_research_pipeline(topic)

            # mark the final step done
            last_title, last_desc = PIPELINE_STEPS[4]
            render_card(card_placeholders[4], 4, last_title, last_desc, "DONE")

            st.session_state.result = result
            st.session_state.ran_topic = topic
            st.toast("Research pipeline complete ✅")
        except Exception as e:
            st.error(f"Something went wrong: {e}")

# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------
result = st.session_state.result

if result:
    st.markdown(
        f'<div class="results-heading">Results for <span class="accent">{st.session_state.ran_topic}</span></div>',
        unsafe_allow_html=True,
    )

    tab_report, tab_search, tab_scraped, tab_critic = st.tabs(
        ["📄 Final Report", "🔍 Search Results", "📖 Scraped Content", "🧐 Critic Feedback"]
    )

    with tab_report:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.markdown(result.get("report", "_No report generated._"))
        st.markdown("</div>", unsafe_allow_html=True)

        st.download_button(
            "⬇️ Download report (.md)",
            data=str(result.get("report", "")),
            file_name=f"{st.session_state.ran_topic.replace(' ', '_')}_report.md",
            mime="text/markdown",
        )

    with tab_search:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.markdown(result.get("search_results", "_No search results._"))
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_scraped:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.markdown(result.get("scraped_content", "_No scraped content._"))
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_critic:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.markdown(result.get("feedback", "_No critic feedback._"))
        st.markdown("</div>", unsafe_allow_html=True)