# backend/chat/chat_history.py
import os
import sqlite3
from typing import List, Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/chat", tags=["Chat"])

# =========================
# DB Ayarları
# =========================
DB_PATH = os.getenv("CHAT_DB_PATH", os.path.join(os.getcwd(), "chat.db"))
USE_LOCAL_TIME = os.getenv("USE_LOCAL_TIME", "0") in ("1", "true", "True")  # 1 ise Europe/Istanbul kaydet

def get_conn() -> sqlite3.Connection:
    """
    Her çağrıda YENİ bir bağlantı döndürür.
    Global connection/cursor paylaşımı YOK => 'Recursive use of cursors' hatası çözülür.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # WAL modu: daha iyi eşzamanlılık (kalıcıdır ama her bağlantıda ayarlamak zararsız)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def ts_iso() -> str:
    """
    ISO 8601 zaman damgası. Varsayılan UTC; istenirse Europe/Istanbul.
    DeprecationWarning yok (timezone-aware).
    """
    if USE_LOCAL_TIME:
        return datetime.now(ZoneInfo("Europe/Istanbul")).isoformat(timespec="seconds")
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def ensure_schema() -> None:
    """
    Tablo/indeksleri oluşturur. Uygulama import edilirken bir kez çağrılır.
    """
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                message_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      TEXT NOT NULL,
                chat_id      TEXT NOT NULL,
                text         TEXT NOT NULL,
                sender       TEXT NOT NULL,   -- 'user' | 'bot'
                ui_component TEXT,
                timestamp    TEXT             -- ISO 8601 (UTC veya Europe/Istanbul)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                chat_id    TEXT PRIMARY KEY,
                user_id    TEXT NOT NULL,
                title      TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_user_chat ON messages(user_id, chat_id, message_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_updated ON chat_sessions(user_id, updated_at)")
        conn.commit()

# Uygulama import edildiğinde şemayı garanti altına al
ensure_schema()

# =========================
# (MAIN tarafından da kullanılacak) Yardımcılar
# =========================
def save_message_sync(user_id: str, chat_id: str, text: str, sender: str, ui_component_json: Optional[str] = None, timestamp: Optional[str] = None) -> None:
    ts = timestamp or ts_iso()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (user_id, chat_id, text, sender, ui_component, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, chat_id, text, sender, ui_component_json, ts),
        )
        conn.commit()

def ensure_session_exists_sync(chat_id: str, user_id: str, title: str, timestamp: Optional[str] = None) -> None:
    ts = timestamp or ts_iso()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT chat_id FROM chat_sessions WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id)
        ).fetchone()
        if not row:
            conn.execute(
                "INSERT INTO chat_sessions (chat_id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (chat_id, user_id, title, ts, ts),
            )
            conn.commit()

def update_session_updated_at_sync(chat_id: str, user_id: str, timestamp: Optional[str] = None) -> None:
    ts = timestamp or ts_iso()
    with get_conn() as conn:
        conn.execute(
            "UPDATE chat_sessions SET updated_at = ? WHERE chat_id = ? AND user_id = ?",
            (ts, chat_id, user_id)
        )
        conn.commit()

# =========================
# API Endpoints (router)
# =========================
@router.post("/send")
def send_message_api(
    user_id: str,
    chat_id: str,
    text: str,
    sender: str,  # 'user' | 'bot'
    ui_component: Optional[str] = None
):
    save_message_sync(user_id, chat_id, text, sender, ui_component_json=ui_component)
    update_session_updated_at_sync(chat_id, user_id)
    return {"status": "ok"}

@router.get("/messages/{user_id}/{chat_id}")
def get_messages(user_id: str, chat_id: str) -> List[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT message_id, user_id, chat_id, text, sender, ui_component, timestamp "
            "FROM messages WHERE user_id=? AND chat_id=? ORDER BY message_id ASC",
            (user_id, chat_id),
        ).fetchall()
    return [
        {
            "message_id": r["message_id"],
            "user_id": r["user_id"],
            "chat_id": r["chat_id"],
            "text": r["text"],
            "sender": r["sender"],
            "ui_component": r["ui_component"],
            "timestamp": r["timestamp"],
        }
        for r in rows
    ]

@router.get("/sessions/{user_id}")
def get_user_sessions(user_id: str) -> List[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT chat_id, user_id, title, created_at, updated_at "
            "FROM chat_sessions WHERE user_id=? ORDER BY updated_at DESC",
            (user_id,)
        ).fetchall()
    return [
        {
            "chat_id": r["chat_id"],
            "user_id": r["user_id"],
            "title": r["title"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]

@router.post("/session")
def create_session(chat_id: str, user_id: str, title: str):
    ensure_session_exists_sync(chat_id, user_id, title)
    return {"status": "ok"}

@router.put("/session/{chat_id}/title")
def update_session_title(
    chat_id: str,
    title: str = Query(..., description="Yeni başlık"),
    user_id: str = Query(..., description="Kullanıcı ID"),
):
    ts = ts_iso()
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE chat_sessions SET title = ?, updated_at = ? WHERE chat_id = ? AND user_id = ?",
            (title, ts, chat_id, user_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Oturum bulunamadı")
    return {"status": "ok"}

@router.delete("/session/{chat_id}")
def delete_session(chat_id: str, user_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM messages WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        conn.execute("DELETE FROM chat_sessions WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        conn.commit()
    return {"status": "ok"}

# -------------------------
# Arama (eski mesajlarda arama)
# -------------------------
@router.get("/search")
def search_messages(
    user_id: str,
    q: Optional[str] = Query(None, alias="q"),
    query: Optional[str] = Query(None, alias="query"),
    limit: int = 20,
):
    """
    Kullanıcının eski mesajlarında metin araması yapar.
    - Mesaj içeriğinde (messages.text) LIKE araması
    - Son mesaj zamanına göre sıralı
    """
    # Hem q hem query destekle (geriye dönük uyumluluk)
    search_term = q if q is not None else query
    if not search_term:
        raise HTTPException(status_code=422, detail="Missing query parameter: 'q' or 'query'")

    if limit <= 0:
        limit = 20
    if limit > 100:
        limit = 100

    like = f"%{search_term}%"
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT 
                cs.chat_id,
                cs.title       AS chat_title,
                m.message_id,
                m.text         AS message_text,
                m.timestamp,
                m.sender
            FROM chat_sessions cs
            JOIN messages m
              ON cs.chat_id = m.chat_id AND cs.user_id = m.user_id
            WHERE cs.user_id = ?
              AND m.text LIKE ?
            ORDER BY m.timestamp DESC
            LIMIT ?
            """,
            (user_id, like, limit),
        ).fetchall()

    return [
        {
            "chat_id": r["chat_id"],
            "chat_title": r["chat_title"],
            "message_id": r["message_id"],
            "message_text": r["message_text"],
            "timestamp": r["timestamp"],
            "sender": r["sender"],
        }
        for r in rows
    ]