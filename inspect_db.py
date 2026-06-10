"""Quick CLI to inspect what's in meyar.db. Run from the project root:
    python scripts/inspect_db.py
"""
import sys
import os

# Make src/ and config.py importable when run from the project root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import cfg
from src.storage.database import list_runs, load_results


def main():
    runs = list_runs()
    print(f"\n=== Runs in {cfg.DB_PATH} ===")
    if runs.empty:
        print("(no runs yet — run scripts/run_full_evaluation.py first)")
        return

    print(runs.to_string(index=False))

    latest = int(runs.iloc[0]["run_id"])
    rag = load_results("rag_results", latest)
    tqa = load_results("tqa_results", latest)

    print(f"\n=== Latest run (run_id={latest}) ===")
    print(f"RAG results: {len(rag)} rows, {len(rag.columns)} columns")
    print(f"TQA results: {len(tqa)} rows, {len(tqa.columns)} columns")

    if not rag.empty:
        print("\n--- RAG columns ---")
        print(list(rag.columns))
    if not tqa.empty:
        print("\n--- TQA columns ---")
        print(list(tqa.columns))


if __name__ == "__main__":
    main()
