import os
from langchain_ollama import ChatOllama
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# OLLAMA_HOST defaults to localhost (local dev); Docker sets it to http://ollama:11434
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

deepseek_client = ChatOllama(
    model="deepseek-r1:7b",
    temperature=0,
    base_url=OLLAMA_HOST,
    timeout=120
)

llama_client = ChatOllama(
    model="llama3.2",
    temperature=0,
    base_url=OLLAMA_HOST,
    timeout=60
)

# ------------------------------
# 3. عميل الحكم (Judge) - كما هو
# ------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
judge_client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# 4. أسماء النماذج (للتتبع)
# ------------------------------
DEEPSEEK_MODEL = "deepseek-r1:7b"
LLAMA_MODEL = "llama3.2"
JUDGE_MODEL = "gpt-5.5"