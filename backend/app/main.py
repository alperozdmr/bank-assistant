import re ,sys ,os ,time,uuid
from anyio import to_thread
from datetime import datetime
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from common.logging_setup import get_logger
from common.http_middleware import install_http_logging
from common.pii import mask_text

from .auth import router as auth_router
from chat.chat_history import router as chat_router
from agent.agent import handle_message as agent_handle_message

app = FastAPI(title="InterChat API", description="InterChat- Modül 1", version="1.0.0")

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


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: str


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    response: str
    timestamp: datetime
    ui_component: Optional[dict] = None


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
async def chat_endpoint(request: ChatRequest):
    # """ "
    # Chat endpoint'i
    # """

    # # Session ID oluştur veya mevcut olanı kullan
    # session_id = request.session_id or str(uuid.uuid4())

    # # Message ID oluştur
    # message_id = str(uuid.uuid4())

    # # LLM Ajanından yanıt al
    # try:
    #     agent_result = await to_thread.run_sync(agent_handle_message, request.message)
    #     final_text = (
    #         agent_result.get("YANIT")
    #         if isinstance(agent_result, dict)
    #         else None
    #     )
    # except Exception as exc:
    #     final_text = None

    # if not final_text:
    #     final_text = "Şu anda yanıt veremiyorum, lütfen tekrar deneyin."

    # # Yanıttaki <think>...</think> bloklarını temizle
    # def _strip_think(text: str) -> str:
    #     if not isinstance(text, str):
    #         return text
    #     cleaned = re.sub(r"<think\b[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    #     return cleaned.strip()

    # final_text = _strip_think(final_text)

    # response = ChatResponse(
    #     session_id=session_id,
    #     message_id=message_id,
    #     response=final_text,
    #     timestamp=datetime.now(),
    # )
    # return response
    """
    Sade /chat:
    - middleware KULLANMADAN yerel corr_id üretir
    - agent'ı çağırır, hata durumunu yakalar
    - loglar PII maskeli yapılır
    """
    corr_id = str(uuid.uuid4())                  # yerel korelasyon id
    session_id = request.session_id or str(uuid.uuid4())
    message_id = str(uuid.uuid4())

    # giriş logu (kullanıcı mesajını maskeyle)
    log.info("chat_request", extra={
        "event": "chat_request",
        "corr_id": corr_id,
        "user_id": request.user_id,
        "meta": {"session_id": session_id, "message_id": message_id},
        "message_masked": mask_text(request.message),
    })

    # agent/LLM çağrısı
    agent_t0 = time.perf_counter()
    try:
        agent_result = await to_thread.run_sync(agent_handle_message, request.message)
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

  

    # çıkış logu (yanıt maskeli)
    log.info("chat_response", extra={
        "event": "chat_response",
        "corr_id": corr_id,
        "user_id": request.user_id,
        "meta": {"session_id": session_id, "message_id": message_id, "has_ui_component": ui_component is not None},
        "response_masked": mask_text(final_text),
    })
    def _strip_think(text: str) -> str:
        if not isinstance(text, str):
            return text
        cleaned = re.sub(r"<think\b[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
        return cleaned.strip()

    final_text = _strip_think(final_text)
   

    return ChatResponse(
        session_id=session_id,
        message_id=message_id,
        response=final_text,
        timestamp=datetime.now(),
        ui_component=ui_component,
    )