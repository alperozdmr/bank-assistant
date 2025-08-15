import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="InterChat API", description="InterChat- Modül 1", version="1.0.0")
from fastapi.middleware.cors import CORSMiddleware

# -------------------
# CORS Ayarları
# -------------------
origins = ["http://localhost:xxxx", "http://127.0.0.1:xxxx"]  # React frontend portu

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Model
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: str


# Response Model
class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    response: str
    timestamp: datetime


@app.get("/")
async def root():
    return {"message": "InterChat API - InterChat Chatbot"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": "InterChat", "module": "1"}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Temel chat endpoint'i
    Şimdilik basit bir echo response döndürüyor
    """

    # Session ID oluştur veya mevcut olanı kullan
    session_id = request.session_id or str(uuid.uuid4())

    # Message ID oluştur
    message_id = str(uuid.uuid4())

    # Şimdilik basit bir yanıt (daha sonra LLM ile değiştireceğiz)
    bot_response = f"Merhaba! Mesajınızı aldım: '{request.message}'"

    return ChatResponse(
        session_id=session_id,
        message_id=message_id,
        response=bot_response,
        timestamp=datetime.now(),
    )
