import time
from src.generation.clients import deepseek_client, DEEPSEEK_MODEL
from src.evaluation.metrics import track_call_ollama

def ask_deepseek(prompt: str) -> str:
    start = time.time()
    response = deepseek_client.invoke(prompt)  # استخدم invoke بدلاً من create
    latency = time.time() - start
    track_call_ollama(DEEPSEEK_MODEL, response.content, latency)
    return response.content