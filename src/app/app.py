
"""
MEYAR — LLM Evaluation Platform
Streamlit UI — talks to the FastAPI backend in src/api/main.py over HTTP.
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
    page_title="MEYAR — LLM Evaluation Platform",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Theme — dark mode, purple/violet accent
# ============================================================

BG = "#0E0E12"
SURFACE = "#17171D"
SURFACE_2 = "#1E1E26"
BORDER = "#2A2A33"
TEXT = "#F2F2F5"
MUTED = "#9C9CA8"
FAINT = "#65656F"
ACCENT = "#9B6BFF"
ACCENT_HOVER = "#8454F0"
ACCENT_SOFT = "#231C3D"

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {BG}; color: {TEXT}; }}
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}
    h1, h2, h3, h4, p, label, span, div {{ color: {TEXT}; }}

    /* ---- Sidebar — compact ---- */
    section[data-testid="stSidebar"] {{
        background-color: {SURFACE};
        border-right: 1px solid {BORDER};
        min-width: 200px !important;
        max-width: 220px !important;
    }}
    section[data-testid="stSidebar"] > div {{
        padding-top: 0.8rem;
        padding-left: 0.6rem;
        padding-right: 0.6rem;
    }}
    .sidebar-logo-row {{
        display: flex;
        align-items: center;
        gap: 7px;
        padding: 2px 4px 14px 4px;
    }}
    .sidebar-logo-text {{
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 0.01em;
        color: {TEXT};
    }}

    div[data-testid="stSidebarUserContent"] button {{
        background-color: transparent !important;
        border: none !important;
        color: {MUTED} !important;
        text-align: left !important;
        justify-content: flex-start !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        border-radius: 7px !important;
        padding: 6px 9px !important;
        box-shadow: none !important;
        min-height: 0 !important;
    }}
    div[data-testid="stSidebarUserContent"] button:hover {{
        background-color: {SURFACE_2} !important;
        color: {TEXT} !important;
    }}
    div[data-testid="stSidebarUserContent"] button p {{
        font-size: 13px !important;
        font-weight: 500 !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .nav-active button {{ background-color: {ACCENT_SOFT} !important; }}
    .nav-active button p {{ color: {ACCENT} !important; font-weight: 600 !important; }}

    .sidebar-section-label {{
        font-size: 10px;
        font-weight: 600;
        color: {FAINT};
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin: 16px 0 4px 9px;
    }}

    /* ---- Header (main page) ---- */
    .meyar-header {{ display: flex; align-items: baseline; gap: 10px; padding: 2px 0 4px 0; }}
    .meyar-name {{ font-size: 26px; font-weight: 800; letter-spacing: -0.01em; color: {TEXT}; margin: 0; }}
    .meyar-tagline {{ font-size: 13px; font-weight: 500; color: {MUTED}; margin: 0; }}

    /* ---- Upload ---- */
    div[data-testid="stFileUploaderDropzone"] {{
        background-color: {SURFACE} !important;
        border: 1.5px dashed {BORDER} !important;
        border-radius: 10px !important;
    }}
    div[data-testid="stFileUploaderDropzone"]:hover {{ border-color: {ACCENT} !important; }}
    [data-testid="stFileUploaderDropzoneInstructions"] span,
    [data-testid="stFileUploaderDropzoneInstructions"] small {{
        color: {MUTED} !important;
    }}

    /* ---- Buttons ---- */
    div.stButton > button[kind="primary"] {{
        background-color: {ACCENT}; color: {BG}; border: none;
        font-weight: 600; border-radius: 9px; padding: 0.5rem 1.3rem;
    }}
    div.stButton > button[kind="primary"]:hover {{ background-color: {ACCENT_HOVER}; color: white; }}

    /* ---- Model selector: toggle pills instead of checkboxes ---- */
    div[data-testid="stCheckbox"] {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 9px 14px;
        transition: border-color 0.15s ease;
    }}
    div[data-testid="stCheckbox"]:has(input:checked) {{
        background-color: {ACCENT_SOFT};
        border-color: {ACCENT};
    }}
    div[data-testid="stCheckbox"] label p {{
        color: {TEXT} !important;
        font-weight: 500 !important;
        font-size: 13px !important;
    }}
    div[data-testid="stCheckbox"] span[data-baseweb="checkbox"] > div:first-child {{
        background-color: transparent !important;
        border-color: {FAINT} !important;
    }}
    div[data-testid="stCheckbox"]:has(input:checked) span[data-baseweb="checkbox"] > div:first-child {{
        background-color: {ACCENT} !important;
        border-color: {ACCENT} !important;
    }}

    /* ---- Metric cards ---- */
    .metric-card {{
        background-color: {SURFACE}; border: 1px solid {BORDER};
        border-radius: 11px; padding: 14px 16px;
    }}
    .metric-label {{
        font-size: 10px; font-weight: 600; color: {FAINT};
        text-transform: uppercase; letter-spacing: 0.05em; margin: 0 0 5px 0;
    }}
    .metric-value {{ font-size: 19px; font-weight: 700; color: {ACCENT}; margin: 0; }}

    [data-testid="stDataFrame"] {{ border: 1px solid {BORDER}; border-radius: 10px; overflow: hidden; }}

    .streamlit-expanderHeader {{
        background-color: {SURFACE} !important; border-radius: 9px !important;
        border: 1px solid {BORDER} !important; font-weight: 500 !important;
    }}
    div[data-testid="stExpander"] {{ border: none !important; }}

    hr {{ border-color: {BORDER} !important; }}

    .qa-page-card {{
        background-color: {SURFACE}; border: 1px solid {BORDER};
        border-radius: 11px; padding: 16px 18px; margin-bottom: 10px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


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
    model_cols = sorted(set(
        c.rsplit("_", 1)[0] for c in results_df.columns if c.endswith("_answer")
    ))
    metric_suffix_cols = [
        c for c in results_df.columns
        if any(c.startswith(f"{m}_") for m in model_cols) and not c.endswith("_answer")
    ]
    metric_names = sorted(set(
        c.split("_", 1)[1] for m in model_cols for c in metric_suffix_cols if c.startswith(f"{m}_")
    ))
    metric_names = [m for m in metric_names if m not in ("latency_s", "cost_usd")]

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
# Sidebar
# ============================================================

with st.sidebar:
    logo_path = os.path.join(os.path.dirname(__file__),"assets","llogo.png")

    st.image(logo_path, width=140)

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
        st.markdown('<p style="font-size:12px; color:#65656F; padding:4px 9px;">No runs yet</p>', unsafe_allow_html=True)


# ============================================================
# Settings page
# ============================================================

if st.session_state.page == "Settings":
    st.markdown(f'<div class="meyar-header"><span class="meyar-name">Settings</span></div>', unsafe_allow_html=True)
    st.info("No configurable settings yet — this section will be added later.")
    st.stop()


# ============================================================
# Results detail page
# ============================================================

if st.session_state.page == "Results detail":
    st.markdown(
        f"""<div class="meyar-header"><span class="meyar-name">Results detail</span></div>""",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    results_df = st.session_state.results_df
    result = st.session_state.result

    if results_df is None or result is None or results_df.empty:
        st.info("Run an evaluation (or select a past run) to see per-question details here.")
        st.stop()

    comparison_df, model_cols, metric_names = build_comparison_table(results_df)

    st.caption(f"Run #{result['run_id']} · {result['task_type'].upper()} · {len(results_df)} questions")
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
                    st.write(row.get(f"{model_name}_answer", "—"))
                    lat = row.get(f"{model_name}_latency_s", 0)
                    cost = row.get(f"{model_name}_cost_usd", 0)
                    st.caption(f"{lat:.2f}s · ${cost:.6f}")

            if row.get("winner") and pd.notna(row.get("winner")):
                st.markdown(f"**Winner:** {row['winner']}")

    st.stop()


# ============================================================
# New run page (main)
# ============================================================

st.markdown(
    f"""<div class="meyar-header"><span class="meyar-name">MEYAR</span><span class="meyar-tagline">LLM Evaluation Platform</span></div>""",
    unsafe_allow_html=True,
)
st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

st.markdown("**1. Upload your file**")
uploaded_file = st.file_uploader(
    "Upload", type=["csv", "xlsx", "txt", "pdf", "docx"], label_visibility="collapsed",
)

st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
st.markdown("**2. Select models**")

try:
    models_dict = fetch_models()
    model_names_available = list(models_dict.keys())
except Exception:
    model_names_available = []
    st.warning(f"Could not reach the backend at {API_URL} to load the model list.")

selected_models = []
if model_names_available:
    cols = st.columns(min(len(model_names_available), 5))
    for i, model_name in enumerate(model_names_available):
        with cols[i % len(cols)]:
            if st.checkbox(model_name, value=(i < 2), key=f"model_{model_name}"):
                selected_models.append(model_name)

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
                json={"file_path": file_path, "selected_models": selected_models},
                timeout=30,
            )
            eval_r.raise_for_status()
            token_id = eval_r.json()["token_id"]

            with st.spinner("Running evaluation — this can take a few minutes..."):
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

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

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

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    st.markdown("### Metrics by model")

    import plotly.graph_objects as go

    chart_colors = [ACCENT, "#5B3FA8", "#C4B5FD", "#7C5CD9", "#4A2F8C"]
    chart_models = comparison_df["model"].tolist()
    quality_metrics = [m for m in metric_names if m in comparison_df.columns]

    # 3 small charts per row
    for row_start in range(0, len(quality_metrics), 3):
        row_metrics = quality_metrics[row_start:row_start + 3]
        chart_cols = st.columns(len(row_metrics))
        for col, metric in zip(chart_cols, row_metrics):
            with col:
                values = comparison_df[metric].tolist()
                fig = go.Figure(data=[go.Bar(
                    x=chart_models, y=values,
                    marker_color=[chart_colors[j % len(chart_colors)] for j in range(len(chart_models))],
                    text=[f"{v:.2f}" for v in values], textposition="outside",
                )])
                fig.update_layout(
                    title=dict(text=metric.replace("_", " ").title(), font=dict(size=12, color=TEXT)),
                    xaxis=dict(title=None, color=MUTED, gridcolor=BORDER, tickfont=dict(size=10)),
                    yaxis=dict(title=None, color=MUTED, gridcolor=BORDER, tickfont=dict(size=10)),
                    plot_bgcolor=BG, paper_bgcolor=BG,
                    font=dict(color=TEXT, size=10),
                    height=190,
                    margin=dict(l=30, r=10, t=34, b=30),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    st.info("Per-question answers and judge verdicts are available on the **Results detail** page (sidebar).")

else:
    st.info("Upload a file and select models, then click 'Run evaluation' to see results here.")