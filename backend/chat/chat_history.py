import sqlite3
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, FastAPI, Request
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["Chat"])


# -------------------------------
# DB handling for this router
# -------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Open DB connection
    conn = sqlite3.connect("chat.db", check_same_thread=False)
    c = conn.cursor()

    # Create table if it does not exist
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS messages (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        chat_id TEXT NOT NULL,
        text TEXT NOT NULL,
        sender TEXT NOT NULL,
        ui_component TEXT,
        timestamp DATETIME
    )
    """
    )
    
    # Chat sessions tablosu ekle
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS chat_sessions (
        chat_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        created_at DATETIME,
        updated_at DATETIME
    )
    """
    )
    conn.commit()

    app.state.conn = conn
    app.state.c = c

    yield

    # Close DB connection
    c.close()
    conn.close()


# -------------------------------
# Pydantic models
# -------------------------------
class Message(BaseModel):
    user_id: str
    chat_id: str
    text: str
    sender: str  # 'user' veya 'bot'
    ui_component: Optional[str] = None


class ChatSession(BaseModel):
    chat_id: str
    user_id: str
    title: str


# Dependency for DB access
def get_db(request: Request):
    return request.app.state.c, request.app.state.conn


# -------------------------------
# Endpoints
# -------------------------------
@router.post("/send")
def send_message(msg: Message, db=Depends(get_db)):
    c, conn = db
    # GMT+3 zaman damgası oluştur
    from datetime import datetime, timedelta
    gmt_plus_3 = datetime.utcnow() + timedelta(hours=3)
    timestamp = gmt_plus_3.strftime('%Y-%m-%d %H:%M:%S')
    
    c.execute(
        "INSERT INTO messages (user_id, chat_id, text, sender, ui_component, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (msg.user_id, msg.chat_id, msg.text, msg.sender, msg.ui_component, timestamp),
    )
    
    # Chat session'ı güncelle
    c.execute(
        "UPDATE chat_sessions SET updated_at = ? WHERE chat_id = ?",
        (timestamp, msg.chat_id)
    )
    
    conn.commit()
    return {"status": "ok"}


@router.get("/messages/{user_id}/{chat_id}")
def get_messages(user_id: str, chat_id: str, db=Depends(get_db)) -> List[dict]:
    c, _ = db
    c.execute(
        "SELECT message_id, user_id, chat_id, text, sender, ui_component, timestamp FROM messages "
        "WHERE user_id=? AND chat_id=? ORDER BY message_id ASC",
        (user_id, chat_id),
    )
    rows = c.fetchall()
    return [
        {
            "message_id": r[0],
            "user_id": r[1],
            "chat_id": r[2],
            "text": r[3],
            "sender": r[4],
            "ui_component": r[5],
            "timestamp": r[6],
        }
        for r in rows
    ]


@router.get("/sessions/{user_id}")
def get_user_sessions(user_id: str, db=Depends(get_db)) -> List[dict]:
    c, _ = db
    c.execute(
        "SELECT chat_id, user_id, title, created_at, updated_at FROM chat_sessions "
        "WHERE user_id=? ORDER BY updated_at DESC",
        (user_id,)
    )
    rows = c.fetchall()
    return [
        {
            "chat_id": r[0],
            "user_id": r[1],
            "title": r[2],
            "created_at": r[3],
            "updated_at": r[4],
        }
        for r in rows
    ]


@router.post("/session")
def create_session(session: ChatSession, db=Depends(get_db)):
    c, conn = db
    # GMT+3 zaman damgası oluştur
    from datetime import datetime, timedelta
    gmt_plus_3 = datetime.utcnow() + timedelta(hours=3)
    timestamp = gmt_plus_3.strftime('%Y-%m-%d %H:%M:%S')
    
    c.execute(
        "INSERT INTO chat_sessions (chat_id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (session.chat_id, session.user_id, session.title, timestamp, timestamp),
    )
    conn.commit()
    return {"status": "ok"}


@router.put("/session/{chat_id}/title")
def update_session_title(chat_id: str, title: str, user_id: str, db=Depends(get_db)):
    c, conn = db
    # GMT+3 zaman damgası oluştur
    from datetime import datetime, timedelta
    gmt_plus_3 = datetime.utcnow() + timedelta(hours=3)
    timestamp = gmt_plus_3.strftime('%Y-%m-%d %H:%M:%S')
    
    c.execute(
        "UPDATE chat_sessions SET title = ?, updated_at = ? "
        "WHERE chat_id = ? AND user_id = ?",
        (title, timestamp, chat_id, user_id),
    )
    conn.commit()
    return {"status": "ok"}


@router.delete("/session/{chat_id}")
def delete_session(chat_id: str, user_id: str, db=Depends(get_db)):
    c, conn = db
    # Önce mesajları sil
    c.execute(
        "DELETE FROM messages WHERE chat_id = ? AND user_id = ?",
        (chat_id, user_id),
    )
    # Sonra session'ı sil
    c.execute(
        "DELETE FROM chat_sessions WHERE chat_id = ? AND user_id = ?",
        (chat_id, user_id),
    )
    conn.commit()
    return {"status": "ok"}


@router.get("/search")
def search_messages(user_id: str, query: str, db=Depends(get_db)):
    """
    Sohbet başlıklarında ve mesaj içeriklerinde arama yapar
    """
    c, conn = db
    
    # SQL injection'a karşı koruma için parametreli sorgu kullan
    search_query = f"%{query}%"
    
    # Sadece mesaj içeriklerinde arama yap
    c.execute("""
        SELECT DISTINCT 
            cs.chat_id,
            cs.title as chat_title,
            m.message_id,
            m.text as message_text,
            m.timestamp,
            m.sender
        FROM chat_sessions cs
        INNER JOIN messages m ON cs.chat_id = m.chat_id
        WHERE cs.user_id = ? 
        AND m.text LIKE ?
        ORDER BY m.timestamp DESC
        LIMIT 20
    """, (user_id, search_query))
    
    results = []
    for row in c.fetchall():
        chat_id, chat_title, message_id, message_text, timestamp, sender = row
        if message_text:  # Mesaj içeriği varsa ekle
            results.append({
                "chat_id": chat_id,
                "chat_title": chat_title,
                "message_id": message_id,
                "message_text": message_text,
                "timestamp": timestamp,
                "sender": sender
            })
    
    return results
