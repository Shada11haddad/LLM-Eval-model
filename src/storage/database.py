import os
import sqlite3
from datetime import datetime

import pandas as pd

from config import cfg


def get_connection():
    """Open a connection to the meyar.db SQLite file."""
    db_dir = os.path.dirname(cfg.DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(cfg.DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the runs table if it doesn't exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id            INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at        TEXT NOT NULL,
                finished_at       TEXT,
                deepseek_model    TEXT,
                llama_model       TEXT,
                judge_model       TEXT,
                embedding_model   TEXT,
                chunk_size        INTEGER,
                chunk_overlap     INTEGER,
                num_rag_questions INTEGER,
                num_tqa_questions INTEGER,
                notes             TEXT
            )
        """)


def create_run(**kwargs):
    """Insert a new row into `runs` and return its run_id."""
    init_db()
    started_at = datetime.utcnow().isoformat(timespec="seconds")
    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO runs (
                started_at, deepseek_model, llama_model, judge_model,
                embedding_model, chunk_size, chunk_overlap,
                num_rag_questions, num_tqa_questions, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            started_at,
            kwargs.get("deepseek_model"),
            kwargs.get("llama_model"),
            kwargs.get("judge_model"),
            kwargs.get("embedding_model"),
            kwargs.get("chunk_size"),
            kwargs.get("chunk_overlap"),
            kwargs.get("num_rag_questions"),
            kwargs.get("num_tqa_questions"),
            kwargs.get("notes"),
        ))
        return cur.lastrowid


def finish_run(run_id):
    """Stamp the run as finished (called after both DataFrames are saved)."""
    finished_at = datetime.utcnow().isoformat(timespec="seconds")
    with get_connection() as conn:
        conn.execute(
            "UPDATE runs SET finished_at = ? WHERE run_id = ?",
            (finished_at, run_id),
        )


def save_results(df, table_name, run_id):
    """Append a DataFrame to `table_name`, tagging every row with run_id.
    The table is auto-created by pandas on the first write."""
    if df is None or len(df) == 0:
        return 0
    out = df.copy()
    out.insert(0, "run_id", run_id)
    with get_connection() as conn:
        out.to_sql(table_name, conn, if_exists="append", index=False)
    return len(out)


def list_runs():
    """Return every run as a DataFrame (most recent first)."""
    init_db()
    with get_connection() as conn:
        return pd.read_sql("SELECT * FROM runs ORDER BY run_id DESC", conn)


def load_results(table_name, run_id=None):
    """Read evaluation results, optionally filtered to one run."""
    with get_connection() as conn:
        if run_id is None:
            return pd.read_sql(f"SELECT * FROM {table_name}", conn)
        return pd.read_sql(
            f"SELECT * FROM {table_name} WHERE run_id = ?",
            conn, params=(run_id,),
        )
