import time
import random

def polite_sleep():
    time.sleep(random.uniform(1.0, 2.5))

def model_summary(df, model_prefix):
    if df.empty: return {}
    return {
        "avg_latency_s": df[f"{model_prefix}_latency_s"].mean(),
        "total_cost_usd": df[f"{model_prefix}_cost_usd"].sum(),
        "wins": (df["winner"].str.contains(model_prefix, case=False, na=False)).sum() if "winner" in df else None,
    }