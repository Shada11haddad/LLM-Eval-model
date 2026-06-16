import time

from src.generation.clients import get_model_client
from src.evaluation.metrics import track_call, calc_cost
from config import cfg


def generate_answer(model_name: str, prompt: str):

    client = get_model_client(model_name)

    start = time.time()
    response = client.invoke(prompt)
    latency = time.time() - start

    answer = response.content

    usage = getattr(response, "usage_metadata", None) or {}
    tokens_in = usage.get("input_tokens", 0)
    tokens_out = usage.get("output_tokens", 0)

    model_info = cfg.MODELS.get(model_name, {})
    pricing_key = model_info.get("model", model_name)

    cost_usd = calc_cost(tokens_in, tokens_out, pricing_key)

    track_call(
        model_name=model_name,
        latency_s=latency,
        cost_usd=cost_usd,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )

    return answer