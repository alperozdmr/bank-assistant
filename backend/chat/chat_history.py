import sqlite3
from contextlib import asynccontextmanager
from typing import List

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
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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
# Pydantic model
# -------------------------------
class Message(BaseModel):
    user_id: str
    chat_id: str
    text: str


# Dependency for DB access
def get_db(request: Request):
    return request.app.state.c, request.app.state.conn


# -------------------------------
# Endpoints
# -------------------------------
@router.post("/send")
def send_message(msg: Message, db=Depends(get_db)):
    c, conn = db
    c.execute(
        "INSERT INTO messages (user_id, chat_id, text) VALUES (?, ?, ?)",
        (msg.user_id, msg.chat_id, msg.text),
    )
    conn.commit()
    return {"status": "ok"}


@router.get("/messages/{user_id}/{chat_id}")
def get_messages(user_id: str, chat_id: str, db=Depends(get_db)) -> List[dict]:
    c, _ = db
    c.execute(
        "SELECT message_id, user_id, chat_id, text, timestamp FROM messages "
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
            "timestamp": r[4],
        }
        for r in rows
    ]
