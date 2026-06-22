import os
from langchain_openai import ChatOpenAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from dotenv import load_dotenv
from config import cfg

load_dotenv()

# How long to wait on a single model/judge call before giving up (seconds).
# Healthy calls finish in a few seconds, so 60s only ever trips on a stuck call.
REQUEST_TIMEOUT = 60
# Retries for transient blips (e.g. a dropped connection). Worst-case wait on a
# truly stuck call stays bounded at ~REQUEST_TIMEOUT * (1 + MAX_RETRIES).
MAX_RETRIES = 2


def get_model_client(model_key: str):
    """
    model_key: 'deepseek', 'llama', 'qwen', 'gpt4o', 'judge'
    """
    model_info = cfg.MODELS.get(model_key)
    if not model_info:
        raise ValueError(f"Model {model_key} not found in config.MODELS")

    provider = model_info["provider"]
    model_name = model_info["model"]

    if provider == "openai":
        return ChatOpenAI(
            model=model_name,
            temperature=0,
            api_key=cfg.OPENAI_API_KEY,
            timeout=REQUEST_TIMEOUT,
            max_retries=MAX_RETRIES,
        )
    elif provider == "huggingface":
        llm = HuggingFaceEndpoint(
            repo_id=model_name,
            provider=model_info.get("hf_provider", "auto"),
            huggingfacehub_api_token=cfg.HF_TOKEN,
            max_new_tokens=512,
            temperature=0.01,
            timeout=REQUEST_TIMEOUT,
        )
        return ChatHuggingFace(llm=llm)
    else:
        raise ValueError(f"Unknown provider {provider}")


judge_client = get_model_client("judge")


def get_all_models():
    return list(cfg.MODELS.keys())