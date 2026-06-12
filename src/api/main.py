"""
FastAPI server for the LLM Evaluation Platform
------------------------------------------------
Start locally:   uvicorn src.api.main:app --reload --port 8000
Via Docker:      docker compose up  (api service auto-starts)

Endpoints
---------
GET  /health                    — is the API alive?
GET  /status                    — are Ollama + models ready?
GET  /runs                      — list all evaluation runs
GET  /runs/{run_id}             — metadata for one run
GET  /results/rag               — RAG results (all runs, or ?run_id=N)
GET  /results/tqa               — TQA results (all runs, or ?run_id=N)
GET  /results/summary           — win counts + avg latency
GET  /db/info                   — DB file path, size, table row counts
GET  /db/download               — download the raw meyar.db SQLite file
POST /evaluate                  — trigger a new evaluation run (async)
GET  /evaluate/status/{run_id}  — check if a triggered run has finished
"""

import os
import sys
import urllib.request
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, FileResponse

from src.storage.database import list_runs, load_results, get_connection, init_db

app = FastAPI(
    title="LLM Evaluation API",
    description="Query results and trigger evaluations for DeepSeek-R1:7b vs Llama3.2",
    version="1.0.0",
)

# Track background evaluation runs: run_id -> "running" | "done" | "error:<msg>"
_eval_status: dict[int, str] = {}


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
def health():
    """Simple liveness check — returns 200 if the API is up."""
    return {"status": "ok"}


# ── Status ─────────────────────────────────────────────────────────────────────

@app.get("/status", tags=["system"])
def status():
    """
    Check whether Ollama is reachable and both models are available.
    """
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    # Is Ollama reachable?
    try:
        urllib.request.urlopen(f"{ollama_host}/api/tags", timeout=5)
        ollama_ok = True
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"ollama": "unreachable", "error": str(e)},
        )

    # Which models are loaded?
    try:
        import json
        with urllib.request.urlopen(f"{ollama_host}/api/tags", timeout=5) as r:
            data = json.loads(r.read())
        available = [m["name"] for m in data.get("models", [])]
    except Exception:
        available = []

    deepseek_ready = any("deepseek" in m for m in available)
    llama_ready    = any("llama"    in m for m in available)

    return {
        "ollama": "ok" if ollama_ok else "unreachable",
        "models": {
            "deepseek-r1:7b": "ready" if deepseek_ready else "not loaded",
            "llama3.2":       "ready" if llama_ready    else "not loaded",
        },
        "available_models": available,
    }


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
    """
    RAG evaluation results.
    Pass ?run_id=N to filter to a specific run.
    """
    try:
        df = load_results("rag_results", run_id)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/results/tqa", tags=["results"])
def get_tqa_results(run_id: Optional[int] = None):
    """
    TruthfulQA evaluation results.
    Pass ?run_id=N to filter to a specific run.
    """
    try:
        df = load_results("tqa_results", run_id)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/results/summary", tags=["results"])
def get_summary(run_id: Optional[int] = None):
    """
    Win counts and average latency for both models.
    Covers both RAG and TQA. Pass ?run_id=N to filter.
    """
    def summarise(df, label):
        if df.empty:
            return {"questions": 0}
        wins_ds = int(df["winner"].str.lower().str.contains("deepseek", na=False).sum())
        wins_ll = int(df["winner"].str.lower().str.contains("llama",    na=False).sum())
        return {
            "questions": len(df),
            "deepseek_wins": wins_ds,
            "llama_wins":    wins_ll,
            "deepseek_avg_latency_s": round(float(df["deepseek_latency_s"].mean()), 2),
            "llama_avg_latency_s":    round(float(df["llama_latency_s"].mean()),    2),
        }

    try:
        rag = load_results("rag_results", run_id)
        tqa = load_results("tqa_results", run_id)
        return {
            "run_id": run_id or "all",
            "rag": summarise(rag, "rag"),
            "tqa": summarise(tqa, "tqa"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Database ───────────────────────────────────────────────────────────────────

@app.get("/db/info", tags=["database"])
def db_info():
    """
    Show the SQLite DB file path, size, and row counts per table.
    """
    from config import cfg
    db_path = cfg.DB_PATH

    if not os.path.exists(db_path):
        return {"db_path": db_path, "exists": False, "size_mb": 0, "tables": {}}

    size_mb = round(os.path.getsize(db_path) / 1024 / 1024, 3)

    import sqlite3
    with sqlite3.connect(db_path) as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        counts = {}
        for (t,) in tables:
            row = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()
            counts[t] = row[0]

    return {"db_path": db_path, "exists": True, "size_mb": size_mb, "tables": counts}


@app.get("/db/download", tags=["database"])
def db_download():
    """
    Download the raw meyar.db SQLite file.
    Open it locally with DB Browser for SQLite or any SQLite viewer.
    """
    from config import cfg
    db_path = cfg.DB_PATH

    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="meyar.db not found — run an evaluation first.")

    return FileResponse(
        path=db_path,
        filename="meyar.db",
        media_type="application/octet-stream",
    )


# ── Trigger evaluation ─────────────────────────────────────────────────────────

def _run_evaluation() -> int:
    """Run the full evaluation in a background thread. Returns run_id."""
    import importlib.util, pathlib
    script = pathlib.Path(__file__).parent.parent.parent / "scripts" / "run_full_evaluation.py"
    spec = importlib.util.spec_from_file_location("run_full_evaluation", script)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()


@app.post("/evaluate", tags=["evaluation"], status_code=202)
def trigger_evaluation(background_tasks: BackgroundTasks):
    """
    Start a new evaluation run in the background.
    Returns immediately with a placeholder run_id.
    Poll GET /evaluate/status/{run_id} to check progress.
    """
    # We don't know the actual run_id until the script creates it,
    # so we use a simple thread-level token.
    token_id = len(_eval_status) + 1
    _eval_status[token_id] = "running"

    def _job():
        try:
            _run_evaluation()
            _eval_status[token_id] = "done"
        except Exception as e:
            _eval_status[token_id] = f"error: {e}"

    background_tasks.add_task(_job)

    return {
        "message": "Evaluation started",
        "token_id": token_id,
        "poll": f"/evaluate/status/{token_id}",
        "note": "Models download on first run — expect 10-15 min before results appear.",
    }


@app.get("/evaluate/status/{token_id}", tags=["evaluation"])
def evaluation_status(token_id: int):
    """Check the status of a triggered evaluation run."""
    if token_id not in _eval_status:
        raise HTTPException(status_code=404, detail="Unknown token_id")
    st = _eval_status[token_id]
    return {
        "token_id": token_id,
        "status": st,
        "results_at": "/results/rag and /results/tqa" if st == "done" else None,
    }
