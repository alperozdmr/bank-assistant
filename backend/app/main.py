import uuid
from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware  
from pydantic import BaseModel
from chat.chat_history import router as chat_router
from .auth import router as auth_router,verify_token

app = FastAPI(title="InterChat API", description="InterChat- Modül 1", version="1.0.0")


# -------------------
# CORS Ayarları
# -------------------
origins = ["http://localhost:5173", "http://127.0.0.1:8000"]  # React frontend portu

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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

#---------------------
# Ana Endpoint'ler
# --------------------

@app.get("/")
async def root():
    return {"message": "InterChat API - InterChat Chatbot"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": "InterChat", "module": "1"}


# --------------------
# Chat Endpoint(Token Gerektiren)
# --------------------
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    customer_no: str = Depends(verify_token)
):
    """
    Chat endpoint'i - Kimlik doğrulama gerektirir.
    """
    #Session ID oluştur veya mevcut olanı kullan
    session_id = request.session_id or str(uuid.uuid4())

    # Mesaj ID oluştur

    message_id = str(uuid.uuid4())

    # Kişiselleştirilmiş yanıt

    bot_response = f"Merhaba {customer_no}, mesajınız: '{request.message}' alındı."

    response= ChatResponse(
        session_id=session_id,
        message_id=message_id,
        response=bot_response,
        timestamp=datetime.now()
    )

    return response