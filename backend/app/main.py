# backend/app/main.py
import re, sys, os, time, uuid, json
from anyio import to_thread
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from common.logging_setup import get_logger
from common.http_middleware import install_http_logging
from common.pii import mask_text

from .auth import router as auth_router, get_current_user
from chat.chat_history import (
    router as chat_router,
    save_message_sync,
    ensure_session_exists_sync,
    update_session_updated_at_sync,
)
from agent.AdvancedAgent import agent_handle_message_async
from mcp_server.tools.general_tools import GeneralTools
from mcp_server.data.sqlite_repo import SQLiteRepository
from config_local import DB_PATH

app = FastAPI(title="InterChat API", description="InterChat- Modül 1", version="1.0.0")

# Logger'ı oluştur
log = get_logger("chat_backend", "chat-backend.log", service="chat-backend")

# 1) Logging middleware'i **ÖNCE** ekle (en dış katman olsun)
install_http_logging(app, logger=log)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(chat_router)
app.include_router(auth_router)

def _strip_think(text: str) -> str:
    if not isinstance(text, str):
        return text
    cleaned = re.sub(r"<think\b[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"</?ask\b[^>]*>", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    chat_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    response: str
    timestamp: str
    ui_component: Optional[dict] = None
    chat_id: str

@app.get("/")
async def root():
    return {"message": "InterChat API - InterChat Chatbot"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": "InterChat", "module": "1"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, current_user: int = Depends(get_current_user)):
    user_id = str(current_user)

    # Chat ID yoksa yeni oluştur
    if not request.chat_id:
        request.chat_id = str(uuid.uuid4())

    # korelasyon
    corr_id = str(uuid.uuid4())
    session_id = request.session_id or str(uuid.uuid4())
    message_id = str(uuid.uuid4())

    # giriş logu
    log.info("chat_request", extra={
        "event": "chat_request",
        "corr_id": corr_id,
        "user_id": user_id,
        "meta": {"session_id": session_id, "message_id": message_id, "chat_id": request.chat_id},
        "message_masked": mask_text(request.message),
    })

    # === DB: kullanıcı mesajını kaydet + session'ı garanti et ===
    try:
        # Başlık için ilk 30 karakteri kullan
        title = request.message[:30] + "..." if len(request.message) > 30 else request.message

        # Tek tek çağrıları threadpool'a atıyoruz (sqlite senkron)
        await to_thread.run_sync(ensure_session_exists_sync, request.chat_id, user_id, title)
        await to_thread.run_sync(save_message_sync, user_id, request.chat_id, request.message, "user", None, None)
        log.info("user_message_saved", extra={
            "user_id": user_id,
            "chat_id": request.chat_id,
            "message_length": len(request.message)
        })
    except Exception as e:
        log.error("database_error", extra={
            "error": str(e),
            "user_id": user_id,
            "chat_id": request.chat_id
        })
        raise

    # === Agent / LLM çağrısı (ASYNC) ===
    agent_t0 = time.perf_counter()
    try:
        agent_result = await agent_handle_message_async(
            request.message,
            customer_id=current_user,
            session_id=session_id,
        )

        #agent_result = await to_thread.run_sync(agent_handle_message, request.message, current_user)
        agent_dur = int((time.perf_counter() - agent_t0) * 1000)
        log.info("agent_response_raw", extra={
            "event": "agent_response_raw",
            "corr_id": corr_id,
            "duration_ms": agent_dur,
            "meta": {"type": str(type(agent_result))},
        })
    except Exception as exc:
        agent_result = None
        agent_dur = int((time.perf_counter() - agent_t0) * 1000)
        log.error("agent_error", extra={
            "event": "agent_error",
            "corr_id": corr_id,
            "duration_ms": agent_dur,
            "error": str(exc),
        })

    # === Cevabı hazırla ===
    ui_component = None
    if isinstance(agent_result, dict) and ("YANIT" in agent_result or "text" in agent_result):
        final_text = agent_result.get("YANIT") or agent_result.get("text") or ""
        ui_component = agent_result.get("ui_component")
    elif isinstance(agent_result, str):
        final_text = agent_result
    else:
        final_text = "Şu anda yanıt veremiyorum, lütfen tekrar deneyin."

    final_text = _strip_think(final_text)

    # === DB: bot mesajını kaydet + session updated_at ===
    try:
        ui_component_json = json.dumps(ui_component) if ui_component else None
        await to_thread.run_sync(save_message_sync, user_id, request.chat_id, final_text, "bot", ui_component_json, None)
        await to_thread.run_sync(update_session_updated_at_sync, request.chat_id, user_id, None)
        log.info("bot_message_saved", extra={
            "user_id": user_id,
            "chat_id": request.chat_id,
            "response_length": len(final_text)
        })
    except Exception as e:
        log.error("bot_message_database_error", extra={
            "error": str(e),
            "user_id": user_id,
            "chat_id": request.chat_id
        })
        raise

    # çıkış logu
    log.info("chat_response", extra={
        "event": "chat_response",
        "corr_id": corr_id,
        "user_id": user_id,
        "meta": {"session_id": session_id, "message_id": message_id, "has_ui_component": ui_component is not None, "chat_id": request.chat_id},
        "response_masked": mask_text(final_text),
    })

    # UI için timestamp (ISO, TZ-aware)
    ts_str = datetime.now(timezone.utc).isoformat(timespec="seconds")

    return ChatResponse(
        session_id=session_id,
        message_id=message_id,
        response=final_text,
        timestamp=ts_str,
        ui_component=ui_component,
        chat_id=request.chat_id,
    )

# Accounts endpoint
@app.get("/accounts")
async def get_user_accounts(current_user: int = Depends(get_current_user)):
    """
    Kullanıcının hesaplarını döndürür.
    """
    try:
        repo = SQLiteRepository(DB_PATH)
        general_tools = GeneralTools(repo)
        result = general_tools.get_accounts(current_user)
        
        if "error" in result:
            return {"error": result["error"]}
        
        return result
    except Exception as e:
        log.error("accounts_fetch_error", extra={
            "error": str(e),
            "user_id": current_user
        })
        return {"error": "Hesaplar alınırken bir hata oluştu"}
