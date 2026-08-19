from uuid import uuid4

from app.models.document import Document
from app.models.document_chunk import DocumentChunk


def create_ready_document(
    db,
    auth_headers,
    client,
):
    user_response = client.get(
        "/api/auth/me",
        headers=auth_headers,
    )

    assert user_response.status_code == 200

    user_id = user_response.json()["id"]

    document = Document(
        owner_id=user_id,
        original_filename="chat-test.pdf",
        stored_filename=(
            f"{uuid4()}-chat-test.pdf"
        ),
        content_type="application/pdf",
        file_size=100,
        storage_path="test_uploads/chat-test.pdf",
        status="ready",
        extracted_text=(
            "React and TypeScript are used for frontend "
            "development. Python and FastAPI are used "
            "for backend development."
        ),
    )

    db.add(document)
    db.flush()

    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        content=(
            "React and TypeScript are used for frontend "
            "development. Python and FastAPI are used "
            "for backend development."
        ),
        character_count=120,
        start_character=0,
        end_character=120,
        embedding=[0.1] * 1536,
    )

    db.add(chunk)
    db.commit()

    return document

def test_create_chat_session(
    client,
    auth_headers,
):
    response = client.post(
        "/api/chat/sessions",
        headers=auth_headers,
        json={
            "title": None,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "New conversation"
    assert "id" in data
    assert "owner_id" in data
    
def test_list_chat_sessions(
    client,
    auth_headers,
):
    create_response = client.post(
        "/api/chat/sessions",
        headers=auth_headers,
        json={
            "title": "Test Chat",
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/chat/sessions",
        headers=auth_headers,
    )

    assert response.status_code == 200

    sessions = response.json()

    assert len(sessions) == 1

    assert sessions[0]["title"] == "Test Chat"

def test_chat_with_documents(
    client,
    auth_headers,
    db,
    monkeypatch,
):
    document = create_ready_document(
        db=db,
        auth_headers=auth_headers,
        client=client,
    )

    session_response = client.post(
        "/api/chat/sessions",
        headers=auth_headers,
        json={
            "title": None,
        },
    )

    assert session_response.status_code == 201

    session_id = session_response.json()["id"]

    def fake_generate_embedding(text):
        return [0.1] * 1536

    def fake_generate_rag_answer(
        question,
        context_chunks,
        conversation_history=None,
    ):
        return (
            "The document mentions React, TypeScript, "
            "Python, and FastAPI."
        )

    monkeypatch.setattr(
        "app.api.routes.chat.generate_embedding",
        fake_generate_embedding,
    )

    monkeypatch.setattr(
        "app.api.routes.chat.generate_rag_answer",
        fake_generate_rag_answer,
    )

    response = client.post(
        (
            f"/api/chat/sessions/"
            f"{session_id}/messages"
        ),
        headers=auth_headers,
        json={
            "question": (
                "What technologies are mentioned?"
            ),
            "document_id": str(document.id),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["answer"]
        == (
            "The document mentions React, TypeScript, "
            "Python, and FastAPI."
        )
    )

    assert len(data["sources"]) >= 1

    assert (
        data["sources"][0]["document_name"]
        == "chat-test.pdf"
    )
    
def test_chat_messages_are_saved(
    client,
    auth_headers,
    db,
    monkeypatch,
):
    document = create_ready_document(
        db=db,
        auth_headers=auth_headers,
        client=client,
    )

    session_response = client.post(
        "/api/chat/sessions",
        headers=auth_headers,
        json={
            "title": None,
        },
    )

    session_id = session_response.json()["id"]

    monkeypatch.setattr(
        "app.api.routes.chat.generate_embedding",
        lambda text: [0.1] * 1536,
    )

    monkeypatch.setattr(
        "app.api.routes.chat.generate_rag_answer",
        lambda question,
        context_chunks,
        conversation_history=None:
            "Mocked AI answer.",
    )

    chat_response = client.post(
        (
            f"/api/chat/sessions/"
            f"{session_id}/messages"
        ),
        headers=auth_headers,
        json={
            "question": "What skills are listed?",
            "document_id": str(document.id),
        },
    )

    assert chat_response.status_code == 200

    history_response = client.get(
        (
            f"/api/chat/sessions/"
            f"{session_id}/messages"
        ),
        headers=auth_headers,
    )

    assert history_response.status_code == 200

    messages = history_response.json()

    assert len(messages) == 2

    assert messages[0]["role"] == "user"
    assert (
        messages[0]["content"]
        == "What skills are listed?"
    )

    assert messages[1]["role"] == "assistant"
    assert (
        messages[1]["content"]
        == "Mocked AI answer."
    )
    
def test_first_question_updates_session_title(
    client,
    auth_headers,
    db,
    monkeypatch,
):
    document = create_ready_document(
        db=db,
        auth_headers=auth_headers,
        client=client,
    )

    session_response = client.post(
        "/api/chat/sessions",
        headers=auth_headers,
        json={
            "title": None,
        },
    )

    session_id = session_response.json()["id"]

    monkeypatch.setattr(
        "app.api.routes.chat.generate_embedding",
        lambda text: [0.1] * 1536,
    )

    monkeypatch.setattr(
        "app.api.routes.chat.generate_rag_answer",
        lambda question,
        context_chunks,
        conversation_history=None:
            "Mocked answer.",
    )

    client.post(
        (
            f"/api/chat/sessions/"
            f"{session_id}/messages"
        ),
        headers=auth_headers,
        json={
            "question": (
                "What technologies are mentioned?"
            ),
            "document_id": str(document.id),
        },
    )

    sessions_response = client.get(
        "/api/chat/sessions",
        headers=auth_headers,
    )

    assert sessions_response.status_code == 200

    sessions = sessions_response.json()

    session = next(
        item
        for item in sessions
        if item["id"] == session_id
    )

    assert session["title"] == (
        "What technologies are mentioned?"
    )
    
def test_delete_chat_session(
    client,
    auth_headers,
):
    create_response = client.post(
        "/api/chat/sessions",
        headers=auth_headers,
        json={
            "title": "Delete Me",
        },
    )

    session_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/api/chat/sessions/{session_id}",
        headers=auth_headers,
    )

    assert delete_response.status_code == 204

    messages_response = client.get(
        (
            f"/api/chat/sessions/"
            f"{session_id}/messages"
        ),
        headers=auth_headers,
    )

    assert messages_response.status_code == 404