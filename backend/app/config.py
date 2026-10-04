import os
from dotenv import load_dotenv

load_dotenv()

# DATABASE
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./scholargraph.db")

# GROBID
GROBID_URL = os.getenv("GROBID_URL", "http://127.0.0.1:8070")
GROBID_TIMEOUT_SECONDS = int(os.getenv("GROBID_TIMEOUT_SECONDS", "120"))

# LLM
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")
LLM_API_KEY = os.getenv("LLM_API_KEY", "sk-placeholder")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))

# ACADEMIC APIS
ACADEMIC_API_TIMEOUT_SECONDS = int(os.getenv("ACADEMIC_API_TIMEOUT_SECONDS", "30"))
ACADEMIC_API_MAX_RETRIES = int(os.getenv("ACADEMIC_API_MAX_RETRIES", "2"))

# UPLOAD
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
CORS_ORIGINS_LIST = [origin.strip() for origin in CORS_ORIGINS.split(",") if origin.strip()]
