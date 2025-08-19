# backend/config_local.py

# MCP (server) ayarları
USE_MCP = True
MCP_SSE_URL = "http://127.0.0.1:8081/sse"

# LLM (OpenAI-compatible / Ollama / HF Router) ayarları
LLM_API_BASE = "https://router.huggingface.co/v1"
LLM_CHAT_PATH = "/chat/completions"
LLM_MODEL = "openai/gpt-oss-20b"
LLM_API_KEY = ""  # Hugging Face API anahtarını sitesinden alabilirsiniz