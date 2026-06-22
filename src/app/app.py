"""
MEYAR - LLM Evaluation Platform
Streamlit UI - talks to the FastAPI backend in src/api/main.py over HTTP.
"""

import os
import time

import pandas as pd
import requests
import streamlit as st

# ============================================================
# Backend URL
# ============================================================

API_URL = os.environ.get("API_URL", "http://localhost:8000")

# ============================================================
# Page config
# ============================================================

st.set_page_config(
    page_title="MEYAR - LLM Evaluation Platform",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Theme - dark mode, purple/violet accent
# ============================================================

BG = "#080A10"
BG_2 = "#0D1018"
SIDEBAR = "#10121A"
SURFACE = "#121520"
SURFACE_2 = "#171B28"
SURFACE_3 = "#1C2130"
BORDER = "#2A3040"
BORDER_SOFT = "#202634"
TEXT = "#F6F3FF"
MUTED = "#A6A2B6"
FAINT = "#6F7486"
ACCENT = "#8B5CF6"
ACCENT_2 = "#A78BFA"
ACCENT_HOVER = "#7C3AED"
ACCENT_SOFT = "#21183B"
SUCCESS = "#34D399"

st.markdown(
    f"""
    <style>
    :root {{
        --bg: {BG};
        --bg-2: {BG_2};
        --sidebar: {SIDEBAR};
        --surface: {SURFACE};
        --surface-2: {SURFACE_2};
        --surface-3: {SURFACE_3};
        --border: {BORDER};
        --border-soft: {BORDER_SOFT};
        --text: {TEXT};
        --muted: {MUTED};
        --faint: {FAINT};
        --accent: {ACCENT};
        --accent-2: {ACCENT_2};
        --accent-hover: {ACCENT_HOVER};
        --accent-soft: {ACCENT_SOFT};
    }}

    .stApp {{
        background:
            radial-gradient(circle at 72% 8%, rgba(139, 92, 246, 0.12), transparent 32rem),
            radial-gradient(circle at 28% 0%, rgba(56, 189, 248, 0.055), transparent 28rem),
            linear-gradient(180deg, var(--bg-2) 0%, var(--bg) 46%, #07080D 100%);
        color: var(--text);
    }}

    html, body, [class*="css"] {{
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    h1, h2, h3, h4, h5, h6, p, label, span, div {{
        color: var(--text);
        letter-spacing: 0;
    }}

    .block-container {{
        max-width: 1340px;
        padding-top: 3.1rem;
        padding-bottom: 4rem;
        padding-left: 4.2rem;
        padding-right: 4.2rem;
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}

    [data-testid="stToolbar"] {{
        right: 1rem;
    }}

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {{
        background:
            radial-gradient(circle at 48% 10%, rgba(139, 92, 246, 0.12), transparent 12rem),
            var(--sidebar);
        border-right: 1px solid var(--border);
        min-width: 260px !important;
        max-width: 280px !important;
    }}

    section[data-testid="stSidebar"] > div {{
        padding: 2.1rem 1.35rem 1.3rem 1.35rem;
    }}

    .sidebar-brand {{
        margin: 0 0 3.15rem 0;
        padding: 0 0.35rem;
    }}

    .sidebar-brand-name {{
        margin: 0;
        font-size: 27px;
        line-height: 1;
        font-weight: 800;
        letter-spacing: 0.18em;
        color: var(--text);
    }}

    .sidebar-brand-subtitle {{
        margin: 0.55rem 0 0 0;
        font-size: 13px;
        color: var(--muted);
        font-weight: 500;
    }}

    div[data-testid="stSidebarUserContent"] button {{
        background-color: transparent !important;
        border: 1px solid transparent !important;
        color: var(--muted) !important;
        text-align: left !important;
        justify-content: flex-start !important;
        font-weight: 650 !important;
        font-size: 15px !important;
        border-radius: 8px !important;
        padding: 0.84rem 1rem !important;
        box-shadow: none !important;
        min-height: 3.2rem !important;
        transition: background-color 0.16s ease, border-color 0.16s ease, color 0.16s ease;
    }}

    div[data-testid="stSidebarUserContent"] button:hover {{
        background-color: var(--surface-2) !important;
        border-color: var(--border-soft) !important;
        color: var(--text) !important;
    }}

    div[data-testid="stSidebarUserContent"] button p {{
        font-size: 15px !important;
        font-weight: 650 !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .nav-active button {{
        background:
            linear-gradient(135deg, rgba(139, 92, 246, 0.42), rgba(67, 35, 151, 0.58)) !important;
        border-color: rgba(167, 139, 250, 0.26) !important;
    }}

    .nav-active button p {{
        color: var(--text) !important;
        font-weight: 760 !important;
    }}

    .sidebar-section-label {{
        font-size: 12px;
        font-weight: 750;
        color: var(--faint);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 2.15rem 0 0.7rem 0.1rem;
    }}

    .sidebar-empty {{
        font-size: 13px;
        color: var(--faint);
        padding: 0.25rem 0.35rem;
        margin: 0;
    }}

    /* ---- Header ---- */
    .brand-hero {{
        display: flex;
        align-items: center;
        gap: 1.6rem;
        margin: 0 0 3.1rem 0;
    }}

    .meyar-mark {{
        width: 94px;
        height: 94px;
        position: relative;
        flex: 0 0 auto;
        filter: drop-shadow(0 18px 28px rgba(124, 58, 237, 0.28));
    }}

    .meyar-mark span {{
        position: absolute;
        display: block;
        width: 44px;
        height: 44px;
        border-radius: 12px 18px 12px 22px;
        background:
            linear-gradient(145deg, #B69CFF 0%, #7C3AED 42%, #36009A 100%);
        box-shadow:
            inset 7px 7px 18px rgba(255, 255, 255, 0.16),
            inset -10px -10px 20px rgba(20, 0, 82, 0.45);
    }}

    .meyar-mark span:nth-child(1) {{ left: 8px; top: 4px; transform: rotate(16deg); }}
    .meyar-mark span:nth-child(2) {{ right: 9px; top: 15px; transform: rotate(-10deg); }}
    .meyar-mark span:nth-child(3) {{ left: 11px; bottom: 7px; transform: rotate(-12deg); }}
    .meyar-mark span:nth-child(4) {{ right: 7px; bottom: 1px; transform: rotate(14deg); }}

    .brand-copy {{
        min-width: 0;
    }}

    .meyar-name {{
        margin: 0;
        font-size: clamp(48px, 5.2vw, 76px);
        line-height: 0.93;
        font-weight: 850;
        letter-spacing: 0.08em;
        color: var(--text);
        text-shadow: 0 14px 32px rgba(0, 0, 0, 0.38);
    }}

    .meyar-tagline {{
        margin: 1rem 0 0 0;
        font-size: clamp(19px, 2vw, 28px);
        line-height: 1.25;
        font-weight: 520;
        color: var(--muted);
    }}

    .page-title {{
        font-size: 34px;
        line-height: 1.1;
        font-weight: 800;
        margin: 0 0 1.6rem 0;
    }}

    .step-title {{
        display: block;
        margin: 2.35rem 0 1.35rem 0;
        font-size: 25px;
        line-height: 1.2;
        font-weight: 800;
        color: var(--text);
    }}

    /* ---- Upload ---- */
    div[data-testid="stFileUploader"] {{
        margin-bottom: 0;
    }}

    div[data-testid="stFileUploaderDropzone"] {{
        background:
            linear-gradient(180deg, rgba(18, 21, 32, 0.84), rgba(13, 16, 24, 0.84)) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        padding: 1.8rem 2rem !important;
        min-height: 130px;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
    }}

    div[data-testid="stFileUploaderDropzone"]:hover {{
        border-color: rgba(167, 139, 250, 0.74) !important;
        background-color: var(--surface-2) !important;
    }}

    [data-testid="stFileUploaderDropzoneInstructions"] span {{
        color: var(--text) !important;
        font-size: 19px !important;
        font-weight: 760 !important;
    }}

    [data-testid="stFileUploaderDropzoneInstructions"] small {{
        color: var(--muted) !important;
        font-size: 15px !important;
    }}

    div[data-testid="stFileUploaderDropzone"] button {{
        background: transparent !important;
        border: 1px solid rgba(167, 139, 250, 0.7) !important;
        color: var(--accent-2) !important;
        border-radius: 7px !important;
        font-weight: 750 !important;
        padding: 0.62rem 1rem !important;
    }}

    div[data-testid="stFileUploaderDropzone"] button:hover {{
        border-color: var(--accent-2) !important;
        color: var(--text) !important;
        background-color: rgba(139, 92, 246, 0.12) !important;
    }}

    /* ---- Buttons ---- */
    div.stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, var(--accent), #5B21B6) !important;
        color: white !important;
        border: 1px solid rgba(167, 139, 250, 0.35) !important;
        font-weight: 780 !important;
        border-radius: 8px !important;
        padding: 0.78rem 1.55rem !important;
        box-shadow: 0 16px 34px rgba(91, 33, 182, 0.28) !important;
    }}

    div.stButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, var(--accent-hover), #4C1D95) !important;
        color: white !important;
        border-color: rgba(196, 181, 253, 0.5) !important;
    }}

    /* ---- Model selector ---- */
    .model-card-shell {{
        min-height: 190px;
        border: 1px solid var(--border);
        border-radius: 8px;
        background:
            radial-gradient(circle at 50% 42%, rgba(139, 92, 246, 0.13), transparent 60%),
            linear-gradient(180deg, rgba(18, 21, 32, 0.88), rgba(9, 11, 17, 0.72));
        padding: 1.15rem 1.15rem 1rem 1.15rem;
        margin-bottom: 0.8rem;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
    }}

    .model-card-shell:hover {{
        border-color: rgba(167, 139, 250, 0.5);
    }}

    .model-logo {{
        height: 88px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0.3rem 0 0.75rem 0;
        color: var(--accent-2);
    }}

    .model-logo svg {{
        width: 70px;
        height: 70px;
        filter: drop-shadow(0 18px 26px rgba(91, 33, 182, 0.34));
    }}

    .model-logo-text {{
        font-size: 46px;
        line-height: 1;
        font-weight: 850;
        color: var(--accent-2);
        text-shadow: 0 18px 30px rgba(91, 33, 182, 0.38);
    }}

    div[data-testid="stCheckbox"] {{
        background-color: rgba(18, 21, 32, 0.78);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 0.7rem 0.85rem;
        transition: border-color 0.15s ease, background-color 0.15s ease;
        min-height: 52px;
    }}

    div[data-testid="stCheckbox"]:has(input:checked) {{
        background:
            linear-gradient(135deg, rgba(139, 92, 246, 0.24), rgba(33, 24, 59, 0.9));
        border-color: rgba(167, 139, 250, 0.65);
    }}

    div[data-testid="stCheckbox"] label {{
        align-items: center;
        gap: 0.75rem;
    }}

    div[data-testid="stCheckbox"] label p {{
        color: var(--text) !important;
        font-weight: 760 !important;
        font-size: 17px !important;
        line-height: 1.2 !important;
    }}

    div[data-testid="stCheckbox"] span[data-baseweb="checkbox"] > div:first-child {{
        background-color: transparent !important;
        border-color: var(--faint) !important;
        border-radius: 6px !important;
    }}

    div[data-testid="stCheckbox"]:has(input:checked) span[data-baseweb="checkbox"] > div:first-child {{
        background: linear-gradient(135deg, var(--accent-2), var(--accent)) !important;
        border-color: var(--accent-2) !important;
    }}

    /* ---- Metric cards ---- */
    .metric-card {{
        background:
            linear-gradient(180deg, rgba(24, 28, 41, 0.9), rgba(15, 18, 28, 0.9));
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1.25rem 1.35rem;
        min-height: 96px;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
    }}

    .metric-label {{
        font-size: 13px;
        font-weight: 760;
        color: var(--faint);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 0 0 0.75rem 0;
    }}

    .metric-value {{
        font-size: 21px;
        line-height: 1.15;
        font-weight: 800;
        color: var(--accent-2);
        margin: 0;
    }}

    /* ---- Tables and charts ---- */
    [data-testid="stDataFrame"] {{
        border: 1px solid var(--border);
        border-radius: 8px;
        overflow: hidden;
        background-color: var(--surface);
    }}

    [data-testid="stDataFrame"] div {{
        color: var(--text);
    }}

    .streamlit-expanderHeader {{
        background-color: var(--surface) !important;
        border-radius: 8px !important;
        border: 1px solid var(--border) !important;
        font-weight: 650 !important;
    }}

    div[data-testid="stExpander"] {{
        border: none !important;
    }}

    div[data-testid="stExpander"] details {{
        background: rgba(18, 21, 32, 0.58);
        border: 1px solid var(--border-soft);
        border-radius: 8px;
        overflow: hidden;
    }}

    hr {{
        border-color: var(--border) !important;
        margin: 2rem 0 !important;
    }}

    .stAlert {{
        background-color: rgba(18, 21, 32, 0.88) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text) !important;
    }}

    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {{
        background-color: var(--surface) !important;
        border-color: var(--border) !important;
        border-radius: 8px !important;
        color: var(--text) !important;
    }}

    .qa-page-card {{
        background-color: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1.1rem 1.25rem;
        margin-bottom: 0.9rem;
    }}

    @media (max-width: 900px) {{
        .block-container {{
            padding-left: 1.25rem;
            padding-right: 1.25rem;
            padding-top: 2rem;
        }}

        .brand-hero {{
            gap: 1rem;
            margin-bottom: 2rem;
        }}

        .meyar-mark {{
            width: 68px;
            height: 68px;
        }}

        .meyar-mark span {{
            width: 32px;
            height: 32px;
            border-radius: 9px 13px 9px 16px;
        }}

        .meyar-name {{
            font-size: 42px;
        }}

        .meyar-tagline {{
            font-size: 18px;
            margin-top: 0.55rem;
        }}
        .model-card {{
            min-height: 190px;
            border: 1px solid #2A3040;
            border-radius: 8px;
            background: linear-gradient(180deg, rgba(18, 21, 32, 0.92), rgba(9, 11, 17, 0.78));
            padding: 1.15rem;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            justify-content: space-between;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Small presentation helpers
# ============================================================


def model_logo_html(model_name: str) -> str:
    """Decorative model mark used in the selection cards."""
    name = model_name.lower()
    if "llama" in name or "meta" in name:
        mark = """
        <svg viewBox="0 0 100 100" role="img" aria-label="">
            <path d="M22 58C22 39 35 26 49 48C63 70 76 61 78 45C80 30 62 26 50 49C38 72 20 76 16 59"
                  fill="none" stroke="#2E9BFF" stroke-width="10" stroke-linecap="round"/>
        </svg>
        """
    elif "gpt" in name or "openai" in name:
        mark = """
        <svg viewBox="0 0 100 100" role="img" aria-label="">
            <circle cx="50" cy="50" r="28" fill="none" stroke="#F7F4FF" stroke-width="7"/>
            <path d="M50 18V82M18 50H82M28 28L72 72M72 28L28 72"
                  stroke="#F7F4FF" stroke-width="5" stroke-linecap="round" opacity="0.9"/>
        </svg>
        """
    elif "qwen" in name:
        mark = """
        <svg viewBox="0 0 100 100" role="img" aria-label="">
            <path d="M50 14L82 32V68L50 86L18 68V32Z" fill="none" stroke="#7C6DFF" stroke-width="8"/>
            <path d="M50 14V50L18 68M50 50L82 32M50 50V86" fill="none" stroke="#B7A6FF" stroke-width="6" opacity="0.88"/>
        </svg>
        """
    elif "deepseek" in name:
        mark = """
        <svg viewBox="0 0 100 100" role="img" aria-label="">
            <path d="M22 61C25 34 54 25 70 43C81 55 75 75 56 78C37 81 22 72 22 61Z"
                  fill="none" stroke="#7766FF" stroke-width="9" stroke-linecap="round"/>
            <path d="M58 35C66 28 76 26 84 31M57 36C72 42 79 53 80 66"
                  fill="none" stroke="#8F80FF" stroke-width="7" stroke-linecap="round"/>
            <path d="M39 48L62 74" stroke="#B7A6FF" stroke-width="7" stroke-linecap="round"/>
        </svg>
        """
    else:
        initials = "".join(part[:1] for part in model_name.replace("-", " ").replace("_", " ").split())[:2].upper()
        mark = f'<div class="model-logo-text">{initials or "AI"}</div>'

    return f'<div class="model-logo">{mark}</div>'


def render_brand_hero():
    logo_path = os.path.join(os.path.dirname(__file__),"assets","meyar.png")

    st.image(logo_path, width=250)


def render_page_title(title: str):
    st.markdown(f'<p class="page-title">{title}</p>', unsafe_allow_html=True)


def render_step_title(title: str):
    st.markdown(f'<span class="step-title">{title}</span>', unsafe_allow_html=True)


# ============================================================
# Session state
# ============================================================

defaults = {
    "page": "New run",
    "result": None,
    "results_df": None,
    "summary": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ============================================================
# API helpers
# ============================================================


def api_get(path, **kwargs):
    return requests.get(f"{API_URL}{path}", timeout=kwargs.pop("timeout", 15), **kwargs)


def api_post(path, **kwargs):
    return requests.post(f"{API_URL}{path}", timeout=kwargs.pop("timeout", 60), **kwargs)


@st.cache_data(ttl=10)
def fetch_models():
    r = api_get("/models")
    r.raise_for_status()
    return r.json()


def fetch_runs():
    try:
        r = api_get("/runs")
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def fetch_results(task_type: str, run_id: int):
    path = "/results/rag" if task_type == "rag" else "/results/open_qa"
    r = api_get(path, params={"run_id": run_id})
    r.raise_for_status()
    return pd.DataFrame(r.json())


def fetch_summary(run_id: int):
    r = api_get("/results/summary", params={"run_id": run_id})
    r.raise_for_status()
    return r.json()


def load_run_into_state(run):
    task_type = run.get("task_type", "open_qa")
    run_id = run.get("run_id")
    df = fetch_results(task_type, run_id)
    summary = fetch_summary(run_id)
    st.session_state.result = {"run_id": run_id, "task_type": task_type}
    st.session_state.results_df = df
    st.session_state.summary = summary


def build_comparison_table(results_df: pd.DataFrame):
    model_cols = sorted(
        set(
            c.rsplit("_", 1)[0]
            for c in results_df.columns
            if c.endswith("_answer") and c != "reference_answer"
        )
    )
    metric_suffix_cols = [
        c
        for c in results_df.columns
        if any(c.startswith(f"{m}_") for m in model_cols) and not c.endswith("_answer")
    ]
    metric_names = sorted(
        set(
            c.split("_", 1)[1]
            for m in model_cols
            for c in metric_suffix_cols
            if c.startswith(f"{m}_")
        )
    )
    metric_names = [m for m in metric_names if m not in ("latency_s", "cost_usd")]

    # On the RAG track, RAGAS is authoritative - drop the judge's duplicate
    # faithfulness/relevance so only the RAGAS versions show.
    if "ragas_faithfulness" in metric_names:
        metric_names = [m for m in metric_names if m != "faithfulness"]
    if "ragas_answer_relevancy" in metric_names:
        metric_names = [m for m in metric_names if m != "relevance"]

    rows = []
    for m in model_cols:
        row = {"model": m}
        for metric in metric_names:
            col = f"{m}_{metric}"
            if col in results_df.columns:
                numeric = pd.to_numeric(results_df[col], errors="coerce")
                if numeric.notna().any():
                    row[metric] = round(float(numeric.mean()), 3)
        lat_col = f"{m}_latency_s"
        if lat_col in results_df.columns:
            row["latency_s"] = round(float(results_df[lat_col].mean()), 3)
        cost_col = f"{m}_cost_usd"
        if cost_col in results_df.columns:
            row["cost_usd"] = round(float(results_df[cost_col].sum()), 6)
        rows.append(row)

    return pd.DataFrame(rows), model_cols, metric_names


# ============================================================
# Priority-based model ranking
# ============================================================

LOWER_IS_BETTER = {"cost_usd", "latency_s", "hallucination", "toxicity"}


def rank_models_by_priority(comparison_df, priority_metrics):
    """
    Re-rank models by the user's prioritized metrics.

    comparison_df    : output of build_comparison_table (one row per model).
    priority_metrics : metric names in priority order, most important first,
                       e.g. ["cost_usd", "latency_s", "faithfulness"].

    Returns a DataFrame sorted best -> worst, with 'rank' and 'priority_score'.
    """
    if comparison_df is None or comparison_df.empty or not priority_metrics:
        return pd.DataFrame()

    metrics = [m for m in priority_metrics if m in comparison_df.columns]
    if not metrics:
        return pd.DataFrame()

    df = comparison_df.copy()

    n = len(metrics)
    raw = {m: (n - i) for i, m in enumerate(metrics)}
    total = sum(raw.values())
    weights = {m: w / total for m, w in raw.items()}

    score = pd.Series(0.0, index=df.index)
    for m in metrics:
        col = pd.to_numeric(df[m], errors="coerce")
        lo, hi = col.min(), col.max()
        if pd.isna(lo) or pd.isna(hi) or hi == lo:
            norm = pd.Series(1.0, index=df.index)
        else:
            norm = (col - lo) / (hi - lo)
            if m in LOWER_IS_BETTER:
                norm = 1 - norm
        score += weights[m] * norm.fillna(0.0)

    df["priority_score"] = score.round(4)
    df = df.sort_values("priority_score", ascending=False).reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))
    return df


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <p class="sidebar-brand-name">MEYAR</p>
            <p class="sidebar-brand-subtitle">LLM Evaluation Platform</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for item in ["New run", "Results detail", "Settings"]:
        active = st.session_state.page == item
        st.markdown(f'<div class="{"nav-active" if active else ""}">', unsafe_allow_html=True)
        if st.button(item, key=f"nav_{item}", use_container_width=True):
            st.session_state.page = item
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<p class="sidebar-section-label">Past runs</p>', unsafe_allow_html=True)

    past_runs = fetch_runs()
    if past_runs:
        for run in past_runs[:15]:
            label = run.get("dataset_name") or f"run #{run.get('run_id', '?')}"
            if st.button(label, key=f"past_run_{run.get('run_id')}", use_container_width=True):
                try:
                    load_run_into_state(run)
                    st.session_state.page = "New run"
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not load run: {e}")
    else:
        st.markdown('<p class="sidebar-empty">No runs yet</p>', unsafe_allow_html=True)


# ============================================================
# Settings page  (System & diagnostics)
# ============================================================

if st.session_state.page == "Settings":
    st.markdown(
        '<div class="meyar-header"><span class="meyar-name">Settings</span>'
        '<span class="meyar-tagline">System &amp; diagnostics</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # Clicking this reruns the page, which re-fetches /status and /db/info.
    st.button("↻ Refresh", key="settings_refresh")
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # ---- Provider status (/status) ----
    st.markdown("### Provider status")
    try:
        status = api_get("/status").json()
        pretty = {"openai": "OpenAI", "huggingface": "HuggingFace"}
        for provider, state in status.items():
            s = str(state).lower()
            if s == "ok":
                dot = ACCENT          # reachable
            elif "no" in s and "configured" in s:
                dot = "#E0A050"       # key/token missing
            else:
                dot = "#E05260"       # unreachable / error
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:9px;padding:5px 0;">'
                f'<span style="width:9px;height:9px;border-radius:50%;background:{dot};display:inline-block;"></span>'
                f'<span style="font-weight:600;min-width:120px;">{pretty.get(provider, provider.title())}</span>'
                f'<span style="color:{MUTED};font-size:13px;">{state}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    except Exception as e:
        st.warning(f"Couldn't reach the backend at {API_URL} for provider status. ({e})")

    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

    # ---- Database (/db/info + /db/download) ----
    st.markdown("### Database")
    try:
        info = api_get("/db/info").json()
        if not info.get("exists", False):
            st.info(f"No database yet at `{info.get('db_path', '?')}` — run an evaluation first.")
        else:
            st.markdown(
                f'<div style="color:{MUTED};font-size:13px;margin-bottom:4px;">Path</div>'
                f'<div style="font-family:monospace;font-size:12px;word-break:break-all;'
                f'background:{SURFACE};border:1px solid {BORDER};border-radius:8px;padding:8px 10px;">'
                f'{info["db_path"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

            tables = info.get("tables", {})
            cards = st.columns(len(tables) + 1)
            with cards[0]:
                st.markdown(
                    f'<div class="metric-card"><p class="metric-label">Size</p>'
                    f'<p class="metric-value">{info.get("size_mb", 0)} MB</p></div>',
                    unsafe_allow_html=True,
                )
            for col, (tname, count) in zip(cards[1:], tables.items()):
                with col:
                    st.markdown(
                        f'<div class="metric-card"><p class="metric-label">{tname}</p>'
                        f'<p class="metric-value">{count}</p></div>',
                        unsafe_allow_html=True,
                    )

            st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
            st.markdown(
                f'<a href="{API_URL}/db/download" '
                f'style="display:inline-block;background:{ACCENT};color:{BG};font-weight:600;'
                f'text-decoration:none;padding:8px 16px;border-radius:9px;font-size:13px;">'
                f'Download meyar.db</a>',
                unsafe_allow_html=True,
            )
    except Exception as e:
        st.warning(f"Couldn't reach the backend at {API_URL} for database info. ({e})")

    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

    # ---- Configuration (static — judge is fixed) ----
    st.markdown("### Configuration")
    st.markdown(
        f'<div style="color:{MUTED};font-size:13px;">'
        f'Judge model: <span style="color:{TEXT};font-weight:600;">gpt-5.5</span> (fixed)</div>',
        unsafe_allow_html=True,
    )

    st.stop()


# ============================================================
# Results detail page
# ============================================================

if st.session_state.page == "Results detail":
    render_page_title("Results detail")

    results_df = st.session_state.results_df
    result = st.session_state.result

    if results_df is None or result is None or results_df.empty:
        st.info("Run an evaluation (or select a past run) to see per-question details here.")
        st.stop()

    comparison_df, model_cols, metric_names = build_comparison_table(results_df)

    st.caption(f"Run #{result['run_id']} - {result['task_type'].upper()} - {len(results_df)} questions")
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    for i, row in results_df.iterrows():
        question_preview = str(row.get("question", ""))[:90]
        with st.expander(f"Q{i + 1}: {question_preview}"):
            st.markdown(f"**Question:** {row.get('question', '')}")
            st.markdown(f"**Reference answer:** {row.get('reference_answer', '')}")

            if "context" in row and pd.notna(row.get("context")):
                with st.popover("View retrieved context"):
                    st.write(row["context"])

            st.markdown("---")
            ans_cols = st.columns(len(model_cols)) if model_cols else [st]
            for j, model_name in enumerate(model_cols):
                with ans_cols[j]:
                    st.markdown(f"**{model_name}**")
                    st.write(row.get(f"{model_name}_answer", "-"))
                    lat = row.get(f"{model_name}_latency_s", 0)
                    cost = row.get(f"{model_name}_cost_usd", 0)
                    st.caption(f"{lat:.2f}s - ${cost:.6f}")

            if row.get("winner") and pd.notna(row.get("winner")):
                st.markdown(f"**Winner:** {row['winner']}")

    st.stop()


# ============================================================
# New run page (main)
# ============================================================

render_brand_hero()

render_step_title("1. Upload your file")
uploaded_file = st.file_uploader(
    "Upload",
    type=["csv", "xlsx", "txt", "pdf", "docx"],
    label_visibility="collapsed",
)

render_step_title("2. Select models")

try:
    models_dict = fetch_models()
    model_names_available = list(models_dict.keys())
except Exception:
    model_names_available = []
    st.warning(f"Could not reach the backend at {API_URL} to load the model list.")


selected_models = []

if model_names_available:
    cols = st.columns(min(len(model_names_available), 4))

    for i, model_name in enumerate(model_names_available):

        with cols[i % len(cols)]:
            st.markdown('<div class="model-card">', unsafe_allow_html=True)

            checked = st.checkbox(
                model_name,
                value=(i < 2),
                key=f"model_{model_name}",
            )


            st.markdown('</div>', unsafe_allow_html=True)

            if checked:
                selected_models.append(model_name)

st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

# ---- Advanced options (per-run overrides) ----
with st.expander("Advanced options"):
    num_questions_input = st.number_input(
        "Number of questions to test on (0 = default)",
        min_value=0,
        max_value=200,
        value=0,
        step=1,
        help="Cap how many questions to evaluate. 0 = default (all, up to 50 for QA files).",
    )
    st.caption("RAG chunking (only affects document / RAG runs):")
    chunk_size_input = st.number_input("Chunk size", min_value=200, max_value=4000, value=2000, step=100)
    chunk_overlap_input = st.number_input("Chunk overlap", min_value=0, max_value=1000, value=200, step=50)

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
run_clicked = st.button("Run evaluation", type="primary")

if run_clicked:
    if uploaded_file is None:
        st.error("Please upload a file before running an evaluation.")
    elif not selected_models:
        st.error("Please select at least one model.")
    else:
        status_box = st.empty()
        try:
            status_box.info("Uploading file...")
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            upload_r = api_post("/upload", files=files, timeout=60)
            upload_r.raise_for_status()
            file_path = upload_r.json()["file_path"]

            status_box.info("Starting evaluation...")
            eval_r = api_post(
                "/evaluate",
                json={
                    "file_path": file_path,
                    "selected_models": selected_models,
                    "chunk_size": int(chunk_size_input),
                    "chunk_overlap": int(chunk_overlap_input),
                    "num_questions": int(num_questions_input)
                    if num_questions_input and num_questions_input > 0
                    else None,
                },
                timeout=30,
            )
            eval_r.raise_for_status()
            token_id = eval_r.json()["token_id"]

            with st.spinner("Running evaluation - this can take a few minutes..."):
                while True:
                    poll_r = api_get(f"/evaluate/status/{token_id}", timeout=15)
                    poll_r.raise_for_status()
                    payload = poll_r.json()
                    status = payload["status"]
                    if status == "done":
                        final_status = payload
                        break
                    if status.startswith("error"):
                        raise RuntimeError(status)
                    time.sleep(2)

            run_info = final_status["result"]
            run_id = run_info["run_id"]
            task_type = run_info["task_type"]

            results_df = fetch_results(task_type, run_id)
            summary = fetch_summary(run_id)

            st.session_state.result = {
                "run_id": run_id,
                "task_type": task_type,
                "total_cost_usd": run_info.get("total_cost_usd", 0),
            }
            st.session_state.results_df = results_df
            st.session_state.summary = summary

            status_box.empty()
            st.success("Evaluation complete")

        except requests.exceptions.ConnectionError:
            status_box.error(f"Could not connect to the backend at {API_URL}.")
        except requests.exceptions.HTTPError as e:
            status_box.error(f"Server error: {e.response.text if e.response is not None else e}")
        except Exception as e:
            status_box.error(f"Something went wrong: {e}")


# ============================================================
# Results summary (metrics + table + small charts)
# ============================================================

result = st.session_state.result
results_df = st.session_state.results_df
summary = st.session_state.summary

if result is not None and results_df is not None and not results_df.empty:
    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
    st.markdown("---")

    task_type = result["task_type"]
    run_id = result["run_id"]
    total_cost = result.get("total_cost_usd")
    if total_cost is None:
        all_costs = (summary or {}).get(task_type, {}).get("total_cost_usd", {})
        total_cost = sum(all_costs.values()) if all_costs else 0

    meta_cols = st.columns(4)
    meta_items = [
        ("Task type", task_type.upper()),
        ("Run ID", str(run_id)),
        ("Questions", str(len(results_df))),
        ("Total cost", f"${total_cost:.6f}"),
    ]
    for col, (label, value) in zip(meta_cols, meta_items):
        with col:
            st.markdown(
                f"""<div class="metric-card"><p class="metric-label">{label}</p><p class="metric-value">{value}</p></div>""",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:22px;'></div>", unsafe_allow_html=True)

    comparison_df, model_cols, metric_names = build_comparison_table(results_df)

    st.markdown("### Comparison table")
    display_df = comparison_df.copy()
    for col in display_df.columns:
        if col == "model":
            continue
        if pd.api.types.is_numeric_dtype(display_df[col]):
            if "cost" in col:
                display_df[col] = display_df[col].apply(lambda v: f"${v:.6f}")
            elif "latency" in col:
                display_df[col] = display_df[col].apply(lambda v: f"{v:.2f}s")
            else:
                display_df[col] = display_df[col].apply(lambda v: f"{v:.2f}")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("<div style='height:22px;'></div>", unsafe_allow_html=True)
    st.markdown("### Metrics by model")

    import plotly.graph_objects as go

    chart_colors = [ACCENT_2, "#6D5BD0", "#C4B5FD", "#4F46E5", "#38BDF8"]
    chart_models = comparison_df["model"].tolist()
    quality_metrics = [m for m in metric_names if m in comparison_df.columns]

    for row_start in range(0, len(quality_metrics), 3):
        row_metrics = quality_metrics[row_start : row_start + 3]
        chart_cols = st.columns(len(row_metrics))
        for col, metric in zip(chart_cols, row_metrics):
            with col:
                values = comparison_df[metric].tolist()
                fig = go.Figure(
                    data=[
                        go.Bar(
                            x=chart_models,
                            y=values,
                            marker_color=[chart_colors[j % len(chart_colors)] for j in range(len(chart_models))],
                            text=[f"{v:.2f}" for v in values],
                            textposition="outside",
                        )
                    ]
                )
                fig.update_layout(
                    title=dict(text=metric.replace("_", " ").title(), font=dict(size=14, color=TEXT)),
                    xaxis=dict(title=None, color=MUTED, gridcolor=BORDER_SOFT, tickfont=dict(size=11)),
                    yaxis=dict(title=None, color=MUTED, gridcolor=BORDER_SOFT, tickfont=dict(size=11)),
                    plot_bgcolor=BG,
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color=TEXT, size=11),
                    height=230,
                    margin=dict(l=34, r=12, t=42, b=34),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------
    # Rank models by your priorities
    # ------------------------------------------------------------
    st.markdown("<div style='height:22px;'></div>", unsafe_allow_html=True)
    st.markdown("### Rank models by your priorities")
    st.caption("Pick the metrics that matter most, in order of importance - the first one you pick counts most.")

    rankable = [c for c in comparison_df.columns if c != "model"]
    priority_metrics = st.multiselect(
        "Priority metrics (selection order = priority)",
        options=rankable,
        default=[],
        key="priority_metrics",
    )

    if priority_metrics:
        ranked = rank_models_by_priority(comparison_df, priority_metrics)
        if not ranked.empty:
            best = ranked.iloc[0]["model"]
            st.success(f"Best model for your priorities: **{best}**")

            show_cols = ["rank", "model", "priority_score"] + priority_metrics
            show = ranked[show_cols].copy()
            for c in priority_metrics:
                if "cost" in c:
                    show[c] = show[c].apply(lambda v: f"${v:.6f}" if pd.notna(v) else "-")
                elif "latency" in c:
                    show[c] = show[c].apply(lambda v: f"{v:.2f}s" if pd.notna(v) else "-")
                else:
                    show[c] = show[c].apply(lambda v: f"{v:.2f}" if pd.notna(v) else "-")
            st.dataframe(show, use_container_width=True, hide_index=True)
    else:
        st.info("Select one or more metrics above to see a personalized model ranking.")

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    st.info("Per-question answers and judge verdicts are available on the **Results detail** page (sidebar).")

else:
    st.info("Upload a file and select models, then click 'Run evaluation' to see results here.")
