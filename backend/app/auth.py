import datetime
import os
from typing import Optional

from config_local import DB_PATH, SECRET_KEY
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import create_engine, text

router = APIRouter(prefix="/auth", tags=["auth"])

# JWT Token Ayarları

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token’ın geçerlilik süresi

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> int: # int döndürecek şekilde güncellendi
    credentials_exception = HTTPException(
        status_code=401,
        detail="Kimlik bilgileri doğrulanamadı",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        customer_id_from_token: str = payload.get("sub") # customer_no yerine customer_id_from_token olarak adlandırıldı
        if customer_id_from_token is None:
            raise credentials_exception
        
        # customer_id_from_token'dan customer_id'yi al
        engine = _get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT customer_id FROM customers WHERE customer_id = :cid LIMIT 1"), # customer_no yerine customer_id kullanıldı
                {"cid": int(customer_id_from_token)}, # cno yerine cid kullanıldı ve int'e çevrildi
            )
            row = result.first()
            if not row:
                raise credentials_exception
            return int(row[0])

    except JWTError as e:
        raise credentials_exception


# Token oluşturma fonksiyonu
def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.UTC) + expires_delta # utcnow() yerine now(datetime.UTC) kullanıldı
    else:
        expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=15) # utcnow() yerine now(datetime.UTC) kullanıldı
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
    customer_id: Optional[int] = None
    token: Optional[str] = None
    message: Optional[str] = None


class UserProfileResponse(BaseModel):
    customer_id: int
    name: str
    surname: str
    email: str
    created_at: str
    customer_no: str
    address: str
    phone: str


# Veritabanı Bağlantısı
def _get_engine():
    database_url = f"sqlite:///{DB_PATH}"
    connect_args = {"check_same_thread": False}
    return create_engine(database_url, future=True, connect_args=connect_args)


# Kimlik Doğrulama Fonksiyonu
def _verify_credentials(customer_no: str, password: str) -> Optional[int]: # int veya None döndürecek şekilde güncellendi
    engine = _get_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT customer_id, password
                    FROM customers
                    WHERE customer_no = :cno
                    LIMIT 1
                    """
                ),
                {"cno": customer_no},
            )
            row = result.first()
            if not row:
                return None
                
            stored_customer_id = int(row[0])
            stored_password = row[1]
                
            if stored_password == password:
                return stored_customer_id
            return None
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {exc}")


# Login Endpoint'i
@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    # Kimlik doğrulama işlemi
    customer_id = _verify_credentials(request.customer_no, request.password)
    if customer_id is None: # customer_id kontrolü eklendi
        raise HTTPException(
            status_code=401, detail="Müşteri numarası veya şifre hatalı"
        )

    # Token oluşturma
    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(customer_id)}, expires_delta=access_token_expires # sub'a customer_id eklendi
    )

    return LoginResponse(
        success=True,
        customer_no=request.customer_no,
        customer_id=customer_id,
        token=access_token,
        message="Giriş başarılı.",
    )


# Logout Endpoint'i (client tarafında token silme)
@router.post("/logout")
def logout():
    # Bu endpoint'te sadece token'ın client tarafında silinmesi beklenir.
    # Server tarafında herhangi bir şey yapılması gerekmez, çünkü JWT stateless'tir.
    return {"message": "Çıkış başarılı."}


# Kullanıcı Profil Bilgilerini Getiren Endpoint
@router.get("/profile", response_model=UserProfileResponse)
def get_user_profile(current_user: int = Depends(get_current_user)):
    """
    Giriş yapmış kullanıcının profil bilgilerini döndürür.
    Password hariç tüm bilgileri içerir.
    """
    engine = _get_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT customer_id, name, surname, email, created_at, 
                           customer_no, address, phone
                    FROM customers
                    WHERE customer_id = :cid
                    LIMIT 1
                    """
                ),
                {"cid": current_user},
            )
            row = result.first()
            if not row:
                raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
            
            return UserProfileResponse(
                customer_id=row[0],
                name=row[1],
                surname=row[2],
                email=row[3],
                created_at=row[4],
                customer_no=row[5],
                address=row[6],
                phone=row[7]
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {exc}")
