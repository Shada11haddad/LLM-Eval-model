import time
from src.generation.clients import llama_client, LLAMA_MODEL
from src.evaluation.metrics import track_call_ollama

def ask_llama(prompt: str) -> str:
    start = time.time()
    response = llama_client.invoke(prompt)
    latency = time.time() - start
    track_call_ollama(LLAMA_MODEL, response.content, latency)
    return response.content