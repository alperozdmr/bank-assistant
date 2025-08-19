import os
import uuid
from datetime import datetime
from typing import Optional

import jose.jwt as jwt 
from fastapi import FastAPI,Depends, HTTPException,status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from chat.chat_history import router as chat_router



from .auth import router as auth_router

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
#--------------------
#Chat router'ı ekle
#--------------------
app.include_router(auth_router)

#--------------------
# Auth Router'ı ekle
#--------------------
app.include_router(auth_router)

# -------------------
# JWT Token Ayarları
# -------------------
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")  
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token’ın geçerlilik süresi 30 dakika sonra tekrar giriş yapılması gerekecek
security = HTTPBearer()


# -------------------
# Token Doğrulama 
# -------------------

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """JWT token'ı doğrular ve kullanıcı bilgilerini döndürür"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        customer_no: str = payload.get("sub")
        if customer_no is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Geçersiz token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return customer_no
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token süresi dolmuş",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token doğrulanamadı",
            headers={"WWW-Authenticate": "Bearer"},
        )

#--------------------
# Request ve Response Modelleri
#--------------------


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: str



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


#--------------------
# Protected Endpoint(Token Gerektiren)
#--------------------

@app.post("/chat",response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """"
    Chat endpoint'i
    """

    #Session ID oluştur veya mevcut olanı kullan
    session_id = request.session_id or str(uuid.uuid4())

    #Message ID oluştur
    message_id = str(uuid.uuid4())

# Kişiselleştirilmiş yanıt
    bot_response = f"Merhaba! Size nasıl yardımcı olabilirim? Mesajınız: '{request.message}'",
    
    response = ChatResponse(
        session_id=session_id,
        message_id=message_id,
        response=bot_response[0],
        timestamp=datetime.now()
    )

@app.get("/profile")
async def get_profile(
    customer_no: str = Depends(verify_token)
):
    """
    Kullanıcı profili bilgilerini döndürür.
    """
   
    return {"customer_no": customer_no, 
    "message": f"Hoş geldiniz {customer_no}!"}
