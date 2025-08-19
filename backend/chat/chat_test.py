# Import the router and lifespan from your chat module
from app.chat import lifespan
from app.chat import router as chat_router
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Create a temporary FastAPI app for testing
app = FastAPI(lifespan=lifespan)
app.include_router(chat_router)

client = TestClient(app)


def test_send_and_get_messages():
    # 1. Send a message
    response = client.post(
        "/chat/send",
        json={"user_id": "user1", "chat_id": "chat1", "text": "Hello, world!"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    # 2. Retrieve messages
    response = client.get("/chat/messages/user1/chat1")
    assert response.status_code == 200

    messages = response.json()
    assert isinstance(messages, list)
    assert len(messages) > 0
    assert messages[0]["user_id"] == "user1"
    assert messages[0]["chat_id"] == "chat1"
    assert messages[0]["text"] == "Hello, world!"
    assert "timestamp" in messages[0]


def test_multiple_messages_order():
    # Send multiple messages
    client.post(
        "/chat/send", json={"user_id": "user1", "chat_id": "chat1", "text": "First"}
    )
    client.post(
        "/chat/send", json={"user_id": "user1", "chat_id": "chat1", "text": "Second"}
    )

    response = client.get("/chat/messages/user1/chat1")
    messages = response.json()

    # Ensure chronological order by message_id
    assert len(messages) >= 2
    assert messages[-2]["text"] == "First"
    assert messages[-1]["text"] == "Second"
