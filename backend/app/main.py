import re ,sys ,os ,time,uuid
from anyio import to_thread
from datetime import datetime
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
from chat.chat_history import router as chat_router, get_db, lifespan as chat_lifespan
from agent.agent import handle_message as agent_handle_message

app = FastAPI(title="InterChat API", description="InterChat- Modül 1", version="1.0.0", lifespan=chat_lifespan)

# Logger'ı oluştur
log = get_logger("chat_backend", "chat-backend.log", service="chat-backend")

# 1) Logging middleware'i **ÖNCE** ekle (en dış katman olsun)
install_http_logging(app, logger=log)
# -------------------
# CORS Ayarları
# -------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --------------------
# Chat router'ı ekle
# --------------------
app.include_router(chat_router)

# --------------------
# Auth Router'ı ekle
# --------------------
app.include_router(auth_router)


# --------------------
# Request ve Response Modelleri
# --------------------


def _strip_think(text: str) -> str:
    if not isinstance(text, str):
        return text
    # <think> bloklarını temizle
    cleaned = re.sub(r"<think\b[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    # <ask> bloklarının içeriğini koru, sadece etiketleri kaldır
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
    timestamp: str # datetime yerine str olarak güncellendi
    ui_component: Optional[dict] = None
    chat_id: str


@app.get("/")
async def root():
    return {"message": "InterChat API - InterChat Chatbot"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": "InterChat", "module": "1"}


# --------------------
# Protected Endpoint(Token Gerektiren)
# --------------------


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, current_user: int = Depends(get_current_user), db=Depends(get_db)):
    user_id = str(current_user) # Token'dan gelen user_id'yi string'e çevir
    
    # Chat ID yoksa yeni oluştur
    if not request.chat_id:
        request.chat_id = str(uuid.uuid4())
    
    """
    Sade /chat:
    - middleware KULLANMADAN yerel corr_id üretir
    - agent'ı çağırır, hata durumunu yakalar
    - loglar PII maskeli yapılır
    - Mesajları veritabanına kaydeder
    """
    corr_id = str(uuid.uuid4())                  # yerel korelasyon id
    session_id = request.session_id or str(uuid.uuid4())
    message_id = str(uuid.uuid4())

    # giriş logu (kullanıcı mesajını maskeyle)
    log.info("chat_request", extra={
        "event": "chat_request",
        "corr_id": corr_id,
        "user_id": user_id,
        "meta": {"session_id": session_id, "message_id": message_id, "chat_id": request.chat_id},
        "message_masked": mask_text(request.message),
    })

    # Kullanıcı mesajını veritabanına kaydet
    c, conn = db
    try:
        # GMT+3 zaman damgası oluştur
        from datetime import datetime, timedelta
        gmt_plus_3 = datetime.utcnow() + timedelta(hours=3)
        timestamp = gmt_plus_3.strftime('%Y-%m-%d %H:%M:%S')
        
        c.execute(
            "INSERT INTO messages (user_id, chat_id, text, sender, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, request.chat_id, request.message, "user", timestamp),
        )
        log.info("user_message_saved", extra={
            "user_id": user_id,
            "chat_id": request.chat_id,
            "message_length": len(request.message)
        })
        
        # Chat session'ı kontrol et ve gerekirse oluştur
        c.execute("SELECT chat_id FROM chat_sessions WHERE chat_id = ? AND user_id = ?", 
                  (request.chat_id, user_id))
        if not c.fetchone():
            # İlk mesaj ise session oluştur
            title = request.message[:30] + "..." if len(request.message) > 30 else request.message
            c.execute(
                "INSERT INTO chat_sessions (chat_id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (request.chat_id, user_id, title, timestamp, timestamp),
            )
            log.info("chat_session_created", extra={
                "chat_id": request.chat_id,
                "user_id": user_id,
                "title": title
            })
        
        conn.commit()
        log.info("database_commit_successful")
    except Exception as e:
        log.error("database_error", extra={
            "error": str(e),
            "user_id": user_id,
            "chat_id": request.chat_id
        })
        conn.rollback()
        raise

    # agent/LLM çağrısı
    agent_t0 = time.perf_counter()
    try:
        agent_result = await to_thread.run_sync(agent_handle_message, request.message, current_user) # current_user kullan
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

    # son metni ve UI component'i çıkar
    ui_component = None
    if isinstance(agent_result, dict) and "YANIT" in agent_result:
        final_text = agent_result["YANIT"]
        ui_component = agent_result.get("ui_component")
    elif isinstance(agent_result, str):
        final_text = agent_result
    else:
        final_text = "Şu anda yanıt veremiyorum, lütfen tekrar deneyin."

    # Bot mesajını veritabanına kaydet
    try:
        # UI component'i JSON string olarak kaydet
        ui_component_json = None
        if ui_component:
            import json
            ui_component_json = json.dumps(ui_component)
        
        # Mesajı DB'ye kaydetmeden önce etiketleri temizle
        final_text = _strip_think(final_text)

        # GMT+3 zaman damgası oluştur
        from datetime import datetime, timedelta
        gmt_plus_3 = datetime.utcnow() + timedelta(hours=3)
        timestamp = gmt_plus_3.strftime('%Y-%m-%d %H:%M:%S')
        
        c.execute(
            "INSERT INTO messages (user_id, chat_id, text, sender, ui_component, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, request.chat_id, final_text, "bot", ui_component_json, timestamp),
        )
        log.info("bot_message_saved", extra={
            "user_id": user_id,
            "chat_id": request.chat_id,
            "response_length": len(final_text)
        })
        
        # Chat session'ı güncelle
        c.execute(
            "UPDATE chat_sessions SET updated_at = ? WHERE chat_id = ?",
            (timestamp, request.chat_id)
        )
        
        conn.commit()
        log.info("bot_message_commit_successful")
    except Exception as e:
        log.error("bot_message_database_error", extra={
            "error": str(e),
            "user_id": user_id,
            "chat_id": request.chat_id
        })
        conn.rollback()
        raise

    # çıkış logu (yanıt maskeli)
    log.info("chat_response", extra={
        "event": "chat_response",
        "corr_id": corr_id,
        "user_id": user_id,
        "meta": {"session_id": session_id, "message_id": message_id, "has_ui_component": ui_component is not None, "chat_id": request.chat_id},
        "response_masked": mask_text(final_text),
    })
   
    response = ChatResponse(
        session_id=session_id,
        message_id=message_id,
        response=final_text,
        timestamp=datetime.now().isoformat(), # isoformat() eklendi
        ui_component=ui_component,
        chat_id=request.chat_id,
    )
    return response