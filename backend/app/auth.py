import datetime
import os
from typing import Optional

import jose.jwt as jwt
from config_local import DB_PATH
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text

router = APIRouter(prefix="/auth", tags=["auth"])

# JWT Token Ayarları
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")  # Güvenli bir anahtar kullanın.
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token’ın geçerlilik süresi


# Token oluşturma fonksiyonu
def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Pydantic Modelleri
class LoginRequest(BaseModel):
    customer_no: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    customer_no: Optional[str] = None
    token: Optional[str] = None
    message: Optional[str] = None


# Veritabanı Bağlantısı
def _get_engine():
    database_url = DB_PATH
    connect_args = (
        {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    )
    return create_engine(database_url, future=True, connect_args=connect_args)


# Kimlik Doğrulama Fonksiyonu
def _verify_credentials(customer_no: str, password: str) -> bool:
    engine = _get_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT password
                    FROM customers
                    WHERE customer_no = :cno
                    LIMIT 1
                    """
                ),
                {"cno": customer_no},
            )
            row = result.first()
            if not row:
                return False
            stored_password = row[0]
            return stored_password == password
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {exc}")


# Login Endpoint'i
@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    # Kimlik doğrulama işlemi
    if not _verify_credentials(request.customer_no, request.password):
        raise HTTPException(
            status_code=401, detail="Müşteri numarası veya şifre hatalı"
        )

    # Token oluşturma
    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.customer_no}, expires_delta=access_token_expires
    )

    return LoginResponse(
        success=True,
        customer_no=request.customer_no,
        token=access_token,
        message="Giriş başarılı.",
    )


# Logout Endpoint'i (client tarafında token silme)
@router.post("/logout")
def logout():
    # Bu endpoint'te sadece token’ın client tarafında silinmesi beklenir.
    # Server tarafında herhangi bir şey yapılması gerekmez, çünkü JWT stateless'tir.
    return {"message": "Çıkış başarılı."}
