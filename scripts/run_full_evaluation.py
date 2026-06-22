"""
run_full_evaluation.py — local runner for the NEW (upload-driven) pipeline.

This replaces the old hardcoded DeepSeek-vs-Llama script. It calls the new
run_evaluation() entrypoint on one or more dataset files.

Usage:
    python scripts/run_full_evaluation.py
    python scripts/run_full_evaluation.py data/raw/agriculture_qa.csv
    python scripts/run_full_evaluation.py data/raw/doc.pdf llama qwen
"""

import os
import sys

# Make the project root importable (config.py, src/, storage/ all live there)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pandas as pd
from src.evaluation.run_eval import run_evaluation


# ─────────────────────────────────────────────────────────────
# EDIT THESE
# ─────────────────────────────────────────────────────────────

# Datasets to evaluate. Each one runs as its own evaluation.
#   .csv / .xlsx  (with "question" + "answer" columns)  -> open_qa track
#   .txt / .pdf / .docx                                 -> rag track
DATASETS = [
    "data/raw/agriculture_qa.csv",
    "data/raw/truthfulqa.csv",
    "data/raw/sample_doc.txt",

]

# Models to compare. Any keys from cfg.MODELS EXCEPT "judge".
# e.g. "deepseek", "llama", "qwen", "gpt4o"
SELECTED_MODELS = ["llama", "qwen", "gpt4o", "deepseek"]

# ─────────────────────────────────────────────────────────────


def main():
    # Optional command-line override:
    #   python scripts/run_full_evaluation.py <file> [model1 model2 ...]
    datasets = DATASETS
    models = SELECTED_MODELS
    if len(sys.argv) >= 2:
        datasets = [sys.argv[1]]
    if len(sys.argv) >= 3:
        models = sys.argv[2:]

    print("=" * 60)
    print("LLM Evaluation — Full Run")
    print(f"Models: {models}")
    print("=" * 60)

    for file_path in datasets:
        print(f"\n>>> Dataset: {file_path}")

        if not os.path.exists(file_path):
            print("    SKIPPED — file not found. Add it or fix the path above.")
            continue

        try:
            result = run_evaluation(file_path, models)
        except Exception as e:
            print(f"    FAILED: {type(e).__name__}: {e}")
            continue

        print(f"    Run ID    : {result['run_id']}")
        print(f"    Task type : {result['task_type']}")
        print(f"    Rows      : {len(result['results'])}")
        print(f"    Total cost: ${result['total_cost_usd']:.4f}")

        comp = pd.DataFrame(result["comparison_table"])
        if not comp.empty:
            print("\n    Comparison table:")
            print(comp.to_string(index=False))

    print("\n" + "=" * 60)
    print("Done. Results saved to SQLite (outputs/meyar.db).")
    print("=" * 60)


if __name__ == "__main__":
    main()
