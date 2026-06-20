import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pandas as pd
from src.evaluation.run_eval import run_evaluation

# Models to compare (edit freely)
MODELS = ["llama", "qwen", "gpt4o"]

# Dataset: pass ANY file as the first argument; falls back to truthfulqa.
#   python scripts/prompt_iteration.py data/raw/agriculture_qa.csv
DATASET = sys.argv[1] if len(sys.argv) > 1 else "data/raw/truthfulqa.csv"

# The two prompts to compare. These use {question} (works for any CSV/XLSX QA
# dataset). If DATASET is a RAG document (.txt/.pdf/.docx), add {context} to
# each prompt so the retrieved context gets injected too.
prompt_v1 = "Answer the following question concisely and factually.\n\nQuestion:\n{question}\n\nAnswer:"
prompt_v2 = ("You are a careful expert. Answer ONLY with verified facts, in one sentence. "
             "If you are not sure, say 'I don't know'.\n\nQuestion:\n{question}\n\nAnswer:")

print(f"\nDataset: {DATASET}")
print(f"Models:  {MODELS}")

r1 = run_evaluation(DATASET, MODELS, prompt_template=prompt_v1)
r2 = run_evaluation(DATASET, MODELS, prompt_template=prompt_v2)

print("\n=== PROMPT V1 ==="); print(pd.DataFrame(r1["comparison_table"]).to_string(index=False))
print("\n=== PROMPT V2 ==="); print(pd.DataFrame(r2["comparison_table"]).to_string(index=False))