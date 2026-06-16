import os
import sqlite3
from datetime import datetime

import pandas as pd

from config import cfg


def get_connection():
    db_dir = os.path.dirname(cfg.DB_PATH)

    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(cfg.DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def init_db():

    with get_connection() as conn:

        conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (

            run_id INTEGER PRIMARY KEY AUTOINCREMENT,

            started_at TEXT NOT NULL,
            finished_at TEXT,

            dataset_name TEXT,
            task_type TEXT,

            index_path TEXT,
            chunks_path TEXT,

            judge_model TEXT,
            embedding_model TEXT,

            chunk_size INTEGER,
            chunk_overlap INTEGER,

            num_rag_questions INTEGER,
            num_tqa_questions INTEGER,

            notes TEXT

        )
        """)


def create_run(
    dataset_name=None,
    task_type=None,
    index_path=None,
    chunks_path=None,
    judge_model=None,
    embedding_model=None,
    chunk_size=None,
    chunk_overlap=None,
    num_rag_questions=None,
    num_tqa_questions=None,
    notes=None,
):

    init_db()

    started_at = datetime.utcnow().isoformat(timespec="seconds")

    with get_connection() as conn:

        cur = conn.execute(
            """
            INSERT INTO runs (

                started_at,

                dataset_name,
                task_type,

                index_path,
                chunks_path,

                judge_model,
                embedding_model,

                chunk_size,
                chunk_overlap,

                num_rag_questions,
                num_tqa_questions,

                notes

            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                started_at,

                dataset_name,
                task_type,

                index_path,
                chunks_path,

                judge_model,
                embedding_model,

                chunk_size,
                chunk_overlap,

                num_rag_questions,
                num_tqa_questions,

                notes,
            ),
        )

        return cur.lastrowid


def finish_run(run_id):

    finished_at = datetime.utcnow().isoformat(timespec="seconds")

    with get_connection() as conn:

        conn.execute(
            """
            UPDATE runs
            SET finished_at = ?
            WHERE run_id = ?
            """,
            (finished_at, run_id),
        )


def save_results(df, table_name, run_id):

    if df is None or len(df) == 0:
        return 0

    out = df.copy()

    out.insert(0, "run_id", run_id)

    with get_connection() as conn:

        out.to_sql(table_name,conn,if_exists="replace",index=False)

    return len(out)


def list_runs():

    init_db()

    with get_connection() as conn:

        return pd.read_sql(
            """
            SELECT *
            FROM runs
            ORDER BY run_id DESC
            """,
            conn,
        )


def load_results(table_name, run_id=None):

    with get_connection() as conn:

        if run_id is None:

            return pd.read_sql(
                f"SELECT * FROM {table_name}",
                conn,
            )

        return pd.read_sql(
            f"""
            SELECT *
            FROM {table_name}
            WHERE run_id = ?
            """,
            conn,
            params=(run_id,),
        )