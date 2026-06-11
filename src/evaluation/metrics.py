from config import cfg

def track_call_ollama(model_name: str, answer_text: str, latency_s: float):
    """تتبع استدعاءات Ollama (مجاني، بدون توكنات)"""
    metrics_tracker[model_name] = {
        "tokens_in": 0,
        "tokens_out": 0,
        "cost_usd": 0.0,
        "latency_s": latency_s,
        "latency_label": latency_label(latency_s),
    }
    totals["calls"] += 1

metrics_tracker = {}
totals = {"calls": 0, "tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0}


def calc_cost(usage, model_name: str) -> float:
    rates = cfg.PRICING.get(model_name, {"input": 0.0, "output": 0.0})
    in_tok = getattr(usage, "prompt_tokens", 0) or 0
    out_tok = getattr(usage, "completion_tokens", 0) or 0
    return (in_tok * rates["input"] + out_tok * rates["output"]) / 1_000_000

def latency_label(seconds: float) -> str:
    if seconds < 2: return "Fast"
    elif seconds < 5: return "Medium"
    else: return "Slow"

def track_call(model_name, response, latency_s):
    cost = calc_cost(response.usage, model_name)
    in_tok = response.usage.prompt_tokens
    out_tok = response.usage.completion_tokens
    metrics_tracker[model_name] = {
        "tokens_in": in_tok,
        "tokens_out": out_tok,
        "cost_usd": cost,
        "latency_s": latency_s,
        "latency_label": latency_label(latency_s),
    }
    totals["calls"] += 1
    totals["tokens_in"] += in_tok
    totals["tokens_out"] += out_tok
    totals["cost_usd"] += cost

def get_current_metrics(model_name):
    return dict(metrics_tracker.get(model_name, {}))