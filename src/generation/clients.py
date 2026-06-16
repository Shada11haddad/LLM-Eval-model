import os
from langchain_openai import ChatOpenAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from dotenv import load_dotenv
from config import cfg

load_dotenv()

def get_model_client(model_key: str):
    """
    model_key: 'deepseek', 'llama', 'qwen', 'gpt4o',
    """
    model_info = cfg.MODELS.get(model_key)
    if not model_info:
        raise ValueError(f"Model {model_key} not found in config.MODELS")
    
    provider = model_info["provider"]
    model_name = model_info["model"]
    
    if provider == "openai":
        return ChatOpenAI(model=model_name,temperature=0, api_key=cfg.OPENAI_API_KEY)
    elif provider == "huggingface":
        llm = HuggingFaceEndpoint(
            repo_id=model_name,
            provider=model_info.get("hf_provider", "auto"),
            huggingfacehub_api_token=cfg.HF_TOKEN,
            max_new_tokens=512,
            temperature=0.01,
        )
        return ChatHuggingFace(llm=llm)
    else:
        raise ValueError(f"Unknown provider {provider}")


judge_client = get_model_client("judge")

def get_all_models():
    return list(cfg.MODELS.keys())
