from uuid import uuid4

from app.models.document import Document
from app.models.document_chunk import DocumentChunk


def create_embedded_document(
    db,
    client,
    auth_headers,
    filename: str,
    content: str,
    embedding_value: float,
):
    user_response = client.get(
        "/api/auth/me",
        headers=auth_headers,
    )

    assert user_response.status_code == 200

    user_id = user_response.json()["id"]

    document = Document(
        owner_id=user_id,
        original_filename=filename,
        stored_filename=(
            f"{uuid4()}-{filename}"
        ),
        content_type="application/pdf",
        file_size=100,
        storage_path=(
            f"test_uploads/{filename}"
        ),
        status="ready",
        extracted_text=content,
    )

    db.add(document)
    db.flush()

    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        content=content,
        character_count=len(content),
        start_character=0,
        end_character=len(content),
        embedding=[
            embedding_value
        ] * 1536,
    )

    db.add(chunk)
    db.commit()

    return document, chunk

def create_auth_headers(
    client,
    name: str,
    email: str,
):
    password = "Password123!"

    register_response = client.post(
        "/api/auth/register",
        json={
            "name": name,
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()[
        "access_token"
    ]

    return {
        "Authorization": f"Bearer {token}"
    }
    
def test_semantic_search(
    client,
    auth_headers,
    db,
    monkeypatch,
):
    document, chunk = create_embedded_document(
        db=db,
        client=client,
        auth_headers=auth_headers,
        filename="search-test.pdf",
        content=(
            "React and TypeScript are used "
            "for frontend development."
        ),
        embedding_value=0.1,
    )

    monkeypatch.setattr(
        "app.api.routes.search.generate_embedding",
        lambda text: [0.1] * 1536,
    )

    response = client.post(
        "/api/search/semantic",
        headers=auth_headers,
        json={
            "query": (
                "What frontend technologies "
                "are mentioned?"
            ),
            "limit": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == (
        "What frontend technologies "
        "are mentioned?"
    )

    assert len(data["results"]) >= 1

    result = data["results"][0]

    assert (
        result["document_id"]
        == str(document.id)
    )

    assert (
        result["chunk_id"]
        == str(chunk.id)
    )

    assert (
        "React"
        in result["content"]
    )
    
def test_semantic_search_orders_results(
    client,
    auth_headers,
    db,
    monkeypatch,
):
    first_document, _ = (
        create_embedded_document(
            db=db,
            client=client,
            auth_headers=auth_headers,
            filename="frontend.pdf",
            content=(
                "React and TypeScript "
                "frontend development."
            ),
            embedding_value=0.0,
        )
    )

    second_document, _ = (
        create_embedded_document(
            db=db,
            client=client,
            auth_headers=auth_headers,
            filename="backend.pdf",
            content=(
                "Python and FastAPI "
                "backend development."
            ),
            embedding_value=0.0,
        )
    )

    # Give the chunks explicit vectors.
    chunks = db.query(
        DocumentChunk
    ).all()

    frontend_vector = [0.0] * 1536
    frontend_vector[0] = 1.0

    backend_vector = [0.0] * 1536
    backend_vector[1] = 1.0

    query_vector = [0.0] * 1536
    query_vector[0] = 1.0

    for chunk in chunks:
        if (
            chunk.document_id
            == first_document.id
        ):
            chunk.embedding = (
                frontend_vector
            )

        if (
            chunk.document_id
            == second_document.id
        ):
            chunk.embedding = (
                backend_vector
            )

    db.commit()

    monkeypatch.setattr(
        "app.api.routes.search.generate_embedding",
        lambda text: query_vector,
    )

    response = client.post(
        "/api/search/semantic",
        headers=auth_headers,
        json={
            "query": (
                "Tell me about frontend skills"
            ),
            "limit": 2,
        },
    )

    assert response.status_code == 200

    results = response.json()[
        "results"
    ]

    assert len(results) == 2

    assert (
        results[0]["document_id"]
        == str(first_document.id)
    )
    
def test_semantic_search_respects_limit(
    client,
    auth_headers,
    db,
    monkeypatch,
):
    for index in range(3):
        create_embedded_document(
            db=db,
            client=client,
            auth_headers=auth_headers,
            filename=(
                f"document-{index}.pdf"
            ),
            content=(
                f"Document number {index}"
            ),
            embedding_value=0.1,
        )

    monkeypatch.setattr(
        "app.api.routes.search.generate_embedding",
        lambda text: [0.1] * 1536,
    )

    response = client.post(
        "/api/search/semantic",
        headers=auth_headers,
        json={
            "query": "test query",
            "limit": 2,
        },
    )

    assert response.status_code == 200

    results = response.json()[
        "results"
    ]

    assert len(results) == 2
    
def test_search_does_not_return_other_users_documents(
    client,
    db,
    monkeypatch,
):
    user_a_headers = create_auth_headers(
        client,
        name="Search User A",
        email="searcha@example.com",
    )

    user_b_headers = create_auth_headers(
        client,
        name="Search User B",
        email="searchb@example.com",
    )

    create_embedded_document(
        db=db,
        client=client,
        auth_headers=user_a_headers,
        filename="private-search.pdf",
        content=(
            "Confidential React experience."
        ),
        embedding_value=0.1,
    )

    monkeypatch.setattr(
        "app.api.routes.search.generate_embedding",
        lambda text: [0.1] * 1536,
    )

    response = client.post(
        "/api/search/semantic",
        headers=user_b_headers,
        json={
            "query": "React experience",
            "limit": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["results"] == []
    
def test_semantic_search_requires_authentication(
    client,
):
    response = client.post(
        "/api/search/semantic",
        json={
            "query": "test",
            "limit": 5,
        },
    )

    assert response.status_code == 401