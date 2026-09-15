import os
from dotenv import load_dotenv

load_dotenv()

# GROBID
GROBID_URL = os.getenv("GROBID_URL", "http://127.0.0.1:8070")

# LLM
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai") # openai or local
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini") # default model
LLM_API_KEY = os.getenv("LLM_API_KEY", "sk-placeholder") # Not strictly needed if using Local
LLM_BASE_URL = os.getenv("LLM_BASE_URL", None) # e.g. http://localhost:11434/v1 for Ollama
