# backend/config_local.py

# MCP (server) ayarları
import os

USE_MCP = True
MCP_SSE_URL = "http://127.0.0.1:8081/sse"

# LLM (OpenAI-compatible / Ollama / HF Router) ayarları
LLM_API_BASE = "https://router.huggingface.co/v1"
LLM_CHAT_PATH = "/chat/completions"
LLM_MODEL = "Qwen/Qwen3-30B-A3B:fireworks-ai"
LLM_API_KEY = ""  # Hugging Face API anahtarını sitesinden alabilirsiniz

# JWT Secret Key (Güvenli bir anahtar kullanın)
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.environ.get("BANK_DB_PATH", os.path.join(BASE_DIR, "dummy_bank.db"))
