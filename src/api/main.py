"""
FastAPI server for the LLM Evaluation Platform
------------------------------------------------
Start locally:   uvicorn src.api.main:app --reload --port 8000
Via Docker:      docker compose up  (api service auto-starts)

Endpoints
---------
GET  /health                        — liveness check
GET  /status                        — check OpenAI + HF connectivity
GET  /models                        — list available models for Streamlit UI

POST /upload                        — upload a dataset or document file
POST /evaluate                      — trigger evaluation (file_path, models, prompt)
GET  /evaluate/status/{token_id}    — poll evaluation progress

GET  /runs                          — list all evaluation runs (most recent first)
GET  /runs/{run_id}                 — metadata for one run

GET  /results/rag?run_id=N          — RAG evaluation results
GET  /results/open_qa?run_id=N      — Open QA evaluation results
GET  /results/summary?run_id=N      — win counts + avg latency per model

GET  /db/info                       — DB file path, size, table row counts
GET  /db/download                   — download the raw meyar.db SQLite file
"""

import os
import sys
import shutil
import sqlite3
from typing import Optional, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from config import cfg
from src.storage.database import list_runs, load_results, init_db

app = FastAPI(
    title="LLM Evaluation API",
    description="Run and query LLM evaluations. Designed to be consumed by a Streamlit frontend.",
    version="2.0.0",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
# Allow Streamlit (any origin) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten to your Streamlit URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track background evaluation runs: token_id -> "running" | "done" | "error:<msg>"
_eval_status: dict[int, str] = {}
_eval_results: dict[int, dict] = {}   # store lightweight result summary per token


# ── Pydantic request models ────────────────────────────────────────────────────

class EvaluateRequest(BaseModel):
    file_path: str                          # path returned by POST /upload
    selected_models: List[str]              # e.g. ["deepseek", "llama"]
    prompt_template: Optional[str] = None   # custom prompt; None = use default
    chunk_size: Optional[int] = None        # RAG chunking override; None = cfg default
    chunk_overlap: Optional[int] = None     # RAG chunking override; None = cfg default
    num_questions: Optional[int] = None     # cap on questions to evaluate; None = default


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
def health():
    """Simple liveness check — returns 200 if the API process is running."""
    return {"status": "ok"}


# ── Status ─────────────────────────────────────────────────────────────────────

@app.get("/status", tags=["system"])
def status():
    """
    Check whether the external model providers are reachable.
    Returns provider availability without making a full inference call.
    """
    import httpx

    results = {}

    # OpenAI
    openai_key = cfg.OPENAI_API_KEY
    if openai_key:
        try:
            r = httpx.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {openai_key}"},
                timeout=5,
            )
            results["openai"] = "ok" if r.status_code == 200 else f"error {r.status_code}"
        except Exception as e:
            results["openai"] = f"unreachable: {e}"
    else:
        results["openai"] = "no API key configured"

    # HuggingFace
    hf_token = cfg.HF_TOKEN
    if hf_token:
        try:
            r = httpx.get(
                "https://huggingface.co/api/whoami-v2",
                headers={"Authorization": f"Bearer {hf_token}"},
                timeout=5,
            )
            results["huggingface"] = "ok" if r.status_code == 200 else f"error {r.status_code}"
        except Exception as e:
            results["huggingface"] = f"unreachable: {e}"
    else:
        results["huggingface"] = "no HF token configured"

    return results


# ── Models ─────────────────────────────────────────────────────────────────────

@app.get("/models", tags=["system"])
def get_models():
    """
    List all models available for evaluation (excludes the judge model).
    Streamlit uses this to populate the model-selection widget.
    """
    return {
        name: info
        for name, info in cfg.MODELS.items()
        if name != "judge"
    }


# ── File upload ────────────────────────────────────────────────────────────────

UPLOAD_DIR = os.path.join(cfg.OUTPUTS_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/upload", tags=["evaluation"])
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a dataset (.csv, .json, .jsonl) or document (.pdf, .docx, .txt, .xlsx).
    Returns the saved file path — pass it to POST /evaluate as `file_path`.
    """
    # Must match what detect_task_type / load_document / load_qa_dataset support
    allowed = {".csv", ".xlsx", ".pdf", ".docx", ".txt"}
    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(allowed))}",
        )

    dest = os.path.join(UPLOAD_DIR, file.filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"filename": file.filename, "file_path": dest, "size_bytes": os.path.getsize(dest)}


# ── Trigger evaluation ─────────────────────────────────────────────────────────

def _background_evaluation(token_id: int, file_path: str, selected_models: list, prompt_template: Optional[str],
                           chunk_size: Optional[int], chunk_overlap: Optional[int], num_questions: Optional[int]):
    """Run evaluation in a background thread and record outcome."""
    from src.evaluation.run_eval import run_evaluation
    try:
        result = run_evaluation(
            file_path=file_path,
            selected_models=selected_models,
            prompt_template=prompt_template,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            num_questions=num_questions,
        )
        _eval_results[token_id] = {
            "run_id": result["run_id"],
            "task_type": result["task_type"],
            "table_name": result["table_name"],
            "total_cost_usd": result["total_cost_usd"],
        }
        _eval_status[token_id] = "done"
    except Exception as e:
        _eval_status[token_id] = f"error: {e}"


@app.post("/evaluate", tags=["evaluation"], status_code=202)
def trigger_evaluation(request: EvaluateRequest, background_tasks: BackgroundTasks):
    """
    Start a new evaluation run in the background.

    Body:
        file_path       — path returned by POST /upload
        selected_models — list of model keys, e.g. ["deepseek", "llama", "qwen"]
        prompt_template — optional custom prompt string
        chunk_size      — optional RAG chunk size override
        chunk_overlap   — optional RAG chunk overlap override
        num_questions   — optional cap on number of questions to evaluate

    Returns immediately with a token_id.
    Poll GET /evaluate/status/{token_id} until status is "done".
    """
    if not request.selected_models:
        raise HTTPException(status_code=400, detail="selected_models cannot be empty")

    invalid = [m for m in request.selected_models if m not in cfg.MODELS or m == "judge"]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown or reserved model(s): {invalid}. Available: {list(cfg.MODELS.keys())}",
        )

    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=400, detail=f"file_path not found: {request.file_path}")

    token_id = len(_eval_status) + 1
    _eval_status[token_id] = "running"

    background_tasks.add_task(
        _background_evaluation,
        token_id,
        request.file_path,
        request.selected_models,
        request.prompt_template,
        request.chunk_size,
        request.chunk_overlap,
        request.num_questions,
    )

    return {
        "message": "Evaluation started",
        "token_id": token_id,
        "poll": f"/evaluate/status/{token_id}",
    }


@app.get("/evaluate/status/{token_id}", tags=["evaluation"])
def evaluation_status(token_id: int):
    """
    Poll the status of a triggered evaluation.

    Returns:
        status   — "running" | "done" | "error: <message>"
        result   — summary dict (only present when status == "done")
    """
    if token_id not in _eval_status:
        raise HTTPException(status_code=404, detail=f"Unknown token_id: {token_id}")

    st = _eval_status[token_id]
    resp: dict = {"token_id": token_id, "status": st}

    if st == "done":
        resp["result"] = _eval_results.get(token_id, {})
        resp["results_at"] = "/results/rag or /results/open_qa"

    return resp


# ── Runs ───────────────────────────────────────────────────────────────────────

@app.get("/runs", tags=["results"])
def get_runs():
    """List all evaluation runs, most recent first."""
    try:
        df = list_runs()
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/runs/{run_id}", tags=["results"])
def get_run(run_id: int):
    """Get metadata for a single run."""
    try:
        df = list_runs()
        row = df[df["run_id"] == run_id]
        if row.empty:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        return row.iloc[0].to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Results ────────────────────────────────────────────────────────────────────

@app.get("/results/rag", tags=["results"])
def get_rag_results(run_id: Optional[int] = None):
    """RAG evaluation results. Pass ?run_id=N to filter to a specific run."""
    try:
        df = load_results("rag_results", run_id)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/results/open_qa", tags=["results"])
def get_open_qa_results(run_id: Optional[int] = None):
    """Open QA evaluation results. Pass ?run_id=N to filter to a specific run."""
    try:
        df = load_results("open_qa_results", run_id)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/results/summary", tags=["results"])
def get_summary(run_id: Optional[int] = None):
    """
    Win counts and average latency for all evaluated models.
    Covers both RAG and Open QA. Pass ?run_id=N to filter.
    """
    def _summarise(df):
        if df.empty:
            return {"questions": 0}

        summary = {"questions": len(df)}

        # Count wins per model (winner column contains model name)
        if "winner" in df.columns:
            win_counts = df["winner"].str.lower().value_counts().to_dict()
            summary["wins"] = win_counts

        # Average latency per model (any column ending in _latency_s)
        latency_cols = [c for c in df.columns if c.endswith("_latency_s")]
        summary["avg_latency_s"] = {
            col.replace("_latency_s", ""): round(float(df[col].mean()), 3)
            for col in latency_cols
        }

        # Total cost per model (any column ending in _cost_usd)
        cost_cols = [c for c in df.columns if c.endswith("_cost_usd")]
        summary["total_cost_usd"] = {
            col.replace("_cost_usd", ""): round(float(df[col].sum()), 6)
            for col in cost_cols
        }

        return summary

    try:
        rag = load_results("rag_results", run_id)
        oqa = load_results("open_qa_results", run_id)
        return {
            "run_id": run_id or "all",
            "rag": _summarise(rag),
            "open_qa": _summarise(oqa),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Database ───────────────────────────────────────────────────────────────────

@app.get("/db/info", tags=["database"])
def db_info():
    """Show the SQLite DB file path, size, and row counts per table."""
    db_path = cfg.DB_PATH

    if not os.path.exists(db_path):
        return {"db_path": db_path, "exists": False, "size_mb": 0, "tables": {}}

    size_mb = round(os.path.getsize(db_path) / 1024 / 1024, 3)

    with sqlite3.connect(db_path) as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for (t,) in tables}

    return {"db_path": db_path, "exists": True, "size_mb": size_mb, "tables": counts}


@app.get("/db/download", tags=["database"])
def db_download():
    """Download the raw meyar.db SQLite file."""
    db_path = cfg.DB_PATH

    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="meyar.db not found — run an evaluation first.")

    return FileResponse(
        path=db_path,
        filename="meyar.db",
        media_type="application/octet-stream",
    )