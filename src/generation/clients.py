import os
from langchain_openai import ChatOpenAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from dotenv import load_dotenv
from config import cfg

load_dotenv()

# How long to wait on a single model/judge call before giving up (seconds).
REQUEST_TIMEOUT = 60
MAX_RETRIES = 2


def get_model_client(model_key: str):
    """Return a LangChain chat client for the given model key."""
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


_judge_client = None


class _LazyJudge:
    # Lazy proxy -- initialises the real judge client on first .invoke() call.
    # Avoids crashing imports when the API key is not yet set at import time.
    def invoke(self, *args, **kwargs):
        global _judge_client
        if _judge_client is None:
            _judge_client = get_model_client("judge")
        return _judge_client.invoke(*args, **kwargs)


judge_client = _LazyJudge()


def get_all_models():
    return list(cfg.MODELS.keys())
