import pandas as pd

from src.evaluation.metrics import latency_label


RAG_METRICS = [
    "faithfulness",
    "relevance",
    "coherence",
    "hallucination",
    "toxicity",
    "context_precision",
    "context_recall",
]

OPEN_QA_METRICS = [
    "faithfulness",
    "relevance",
    "coherence",
    "hallucination",
    "toxicity",
]

ALL_METRICS = list(dict.fromkeys(RAG_METRICS + OPEN_QA_METRICS))


def cost_label(total_cost: float):
    if total_cost == 0:
        return "Free"
    elif total_cost < 0.001:
        return "Low"
    elif total_cost < 0.01:
        return "Medium"
    else:
        return "High"


def model_summary(df: pd.DataFrame, model_name: str):

    if df.empty:
        return {}

    summary = {"model": model_name}

    for metric in ALL_METRICS:
        col = f"{model_name}_{metric}"
        if col in df.columns:
            summary[metric] = pd.to_numeric(df[col], errors="coerce").mean()

    latency_col = f"{model_name}_latency_s"
    if latency_col in df.columns:
        avg_latency = df[latency_col].mean()
        summary["latency_s"] = avg_latency
        summary["latency_label"] = latency_label(avg_latency)

    cost_col = f"{model_name}_cost_usd"
    if cost_col in df.columns:
        total_cost = df[cost_col].sum()
        summary["cost_usd"] = total_cost
        summary["cost_label"] = cost_label(total_cost)

    if "winner" in df.columns:
        summary["wins"] = (
            df["winner"]
            .str.contains(model_name, case=False, na=False)
            .sum()
        )

    return summary


def build_comparison_table(df: pd.DataFrame, selected_models: list) -> pd.DataFrame:
    """
    Build a model-comparison table: one row per model, one column per metric.
    """
    rows = [model_summary(df, model_name) for model_name in selected_models]
    return pd.DataFrame(rows)