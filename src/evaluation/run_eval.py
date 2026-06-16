import os
import pandas as pd
from langchain_core.documents import Document
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import cfg
from src.ingestion.loader import detect_task_type, load_qa_dataset, load_document
from src.ingestion.chunker import chunk_documents
from src.retrieval.vectorstore import get_or_build_vectorstore
from src.retrieval.retriever import retrieve, build_rag_prompt
from src.generation.model_router import generate_answer
from src.generation.qa_generation import generate_qa_pairs
from src.evaluation.judge import judge_rag_answers, judge_open_qa_answers
from src.evaluation.parse_verdict import parse_judge_verdict
from src.evaluation.metrics import get_current_metrics, totals
from storage.database import create_run, finish_run, save_results
from src.utils.helpers import build_comparison_table


def _normalize_qa_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map any accepted answer column name to 'reference_answer'"""
    rename_map = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if col_lower in ["answer", "ground_truth", "reference_answer"]:
            rename_map[col] = "reference_answer"
        elif col_lower == "question":
            rename_map[col] = "question"
    return df.rename(columns=rename_map)


def _build_open_qa_prompt(question: str) -> str:
    return f"Answer the following question concisely and factually.\n\nQuestion:\n{question}\n\nAnswer:"


def run_evaluation(file_path: str, selected_models: list):
    """
    Main evaluation entrypoint, called by the FastAPI backend.

    Args:
        file_path: path to the uploaded file (Open QA dataset or RAG document)
        selected_models: list of model keys from cfg.MODELS (e.g. ["gpt4o", "gemini"])
                          must NOT include "judge"

    Returns:
        dict with run_id, task_type, results (list of records), and total cost
    """

    if not selected_models:
        raise ValueError("No models selected for evaluation")

    if "judge" in selected_models:
        raise ValueError("'judge' is reserved and cannot be selected as an evaluated model")

    task_type = detect_task_type(file_path)

    run_id = create_run(
        dataset_name=os.path.basename(file_path),
        task_type=task_type,
        judge_model=cfg.MODELS["judge"]["model"],
        embedding_model=cfg.EMBEDDING_MODEL,
        chunk_size=cfg.CHUNK_SIZE,
        chunk_overlap=cfg.CHUNK_OVERLAP,
    )

    rows = []

    if task_type == "open_qa":

        df = load_qa_dataset(file_path)
        df = _normalize_qa_columns(df)
        if len(df) > 50:
           df = df.sample(n=50, random_state=42)

        for _, row in df.iterrows():
            question = row["question"]
            reference_answer = row["reference_answer"]

            model_answers = {}
            model_metrics = {}
            
            for model_name in selected_models:
                prompt = _build_open_qa_prompt(question)
                answer = generate_answer(model_name, prompt)
                model_answers[model_name] = answer
                model_metrics[model_name] = get_current_metrics(model_name)

            verdict = judge_open_qa_answers(
                question, reference_answer, model_answers, model_metrics
            )
            parsed = parse_judge_verdict(verdict)
            
            row_data = {
                "question": question,
                "reference_answer": reference_answer,
            }
            for model_name in selected_models:
                row_data[f"{model_name}_answer"] = model_answers[model_name]
                row_data[f"{model_name}_latency_s"] = model_metrics[model_name].get("latency_s", 0)
                row_data[f"{model_name}_cost_usd"] = model_metrics[model_name].get("cost_usd", 0)

            row_data["judge_verdict"] = verdict
            row_data.update(parsed)

            rows.append(row_data)

        table_name = "open_qa_results"

    elif task_type == "rag":

        text = load_document(file_path)
        docs = [Document(page_content=text)]
        chunks = chunk_documents(docs)

        index_name = f"run_{run_id}"
        index, indexed_chunks, *_ = get_or_build_vectorstore(index_name, chunks)

        qa_df = generate_qa_pairs(indexed_chunks)

        for _, row in qa_df.iterrows():
            question = row["question"]
            reference_answer = row["reference_answer"]

            retrieved = retrieve(question, index, indexed_chunks, k=3)
            context_chunks = [r["chunk"] for r in retrieved]
            context = "\n\n".join(context_chunks)
            prompt = build_rag_prompt(question, context_chunks)

            model_answers = {}
            model_metrics = {}

            for model_name in selected_models:
                answer = generate_answer(model_name, prompt)
                model_answers[model_name] = answer
                model_metrics[model_name] = get_current_metrics(model_name)

            verdict = judge_rag_answers(
                question, context,reference_answer, model_answers, model_metrics
            )
            parsed = parse_judge_verdict(verdict)

            row_data = {
                "question": question,
                "reference_answer": reference_answer,
                "context": context,
            }
            for model_name in selected_models:
                row_data[f"{model_name}_answer"] = model_answers[model_name]
                row_data[f"{model_name}_latency_s"] = model_metrics[model_name].get("latency_s", 0)
                row_data[f"{model_name}_cost_usd"] = model_metrics[model_name].get("cost_usd", 0)

            row_data["judge_verdict"] = verdict
            row_data.update(parsed)

            rows.append(row_data)

        table_name = "rag_results"

    else:
        raise ValueError(f"Unknown task type: {task_type}")

    results_df = pd.DataFrame(rows)
    save_results(results_df, table_name, run_id)
    finish_run(run_id)
    comparison_df = build_comparison_table(results_df, selected_models)
    return {
        "run_id": run_id,
        "task_type": task_type,
        "table_name": table_name,
        "results": results_df.to_dict(orient="records"),
        "comparison_table": comparison_df.to_dict(orient="records"),
        "total_cost_usd": totals["cost_usd"],
    }