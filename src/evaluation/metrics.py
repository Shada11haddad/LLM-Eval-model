import threading
from config import cfg

metrics_tracker = {}

totals = {"calls": 0, "tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0}
_totals_lock = threading.Lock()


def reset_totals():
    """Call at the start of each evaluation run to clear cross-run accumulation."""
    global metrics_tracker
    with _totals_lock:
        metrics_tracker = {}
        totals["calls"] = 0
        totals["tokens_in"] = 0
        totals["tokens_out"] = 0
        totals["cost_usd"] = 0.0


def latency_label(seconds: float):

    if seconds < 2:
        return "Fast"

    elif seconds < 5:
        return "Medium"

    else:
        return "Slow"


def calc_cost(tokens_in, tokens_out, model_name):

    rates = cfg.PRICING.get(model_name, {"input": 0.0, "output": 0.0})

    return (tokens_in * rates["input"] + tokens_out * rates["output"]) / 1_000_000


def track_call(
    model_name: str,
    latency_s: float,
    cost_usd: float = 0.0,
    tokens_in: int = 0,
    tokens_out: int = 0
):

    metrics_tracker[model_name] = {
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": cost_usd,
        "latency_s": latency_s,
        "latency_label": latency_label(latency_s),
    }

    # Lock so concurrent calls don't lose updates on the += (it's not atomic).
    with _totals_lock:
        totals["calls"] += 1
        totals["tokens_in"] += tokens_in
        totals["tokens_out"] += tokens_out
        totals["cost_usd"] += cost_usd


def get_current_metrics(model_name):

    return dict(metrics_tracker.get(model_name, {}))