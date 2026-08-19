def upload_test_pdf(
    client,
    auth_headers,
    filename="test-document.pdf",
):
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n"
        b"<< /Type /Catalog >>\n"
        b"endobj\n"
        b"trailer\n"
        b"<<>>\n"
        b"%%EOF"
    )

    return client.post(
        "/api/documents/upload",
        headers=auth_headers,
        files={
            "file": (
                filename,
                pdf_content,
                "application/pdf",
            )
        },
    )


def create_auth_headers(
    client,
    name,
    email,
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


def test_upload_document(
    client,
    auth_headers,
):
    response = upload_test_pdf(
        client,
        auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert (
        data["original_filename"]
        == "test-document.pdf"
    )

    assert (
        data["content_type"]
        == "application/pdf"
    )

    assert data["status"] == "uploaded"

    assert "id" in data
    assert "owner_id" in data


def test_list_documents(
    client,
    auth_headers,
):
    upload_response = upload_test_pdf(
        client,
        auth_headers,
        filename="list-test.pdf",
    )

    assert upload_response.status_code == 201

    response = client.get(
        "/api/documents",
        headers=auth_headers,
    )

    assert response.status_code == 200

    documents = response.json()

    assert len(documents) == 1

    assert (
        documents[0]["original_filename"]
        == "list-test.pdf"
    )


def test_get_document_detail(
    client,
    auth_headers,
):
    upload_response = upload_test_pdf(
        client,
        auth_headers,
        filename="detail-test.pdf",
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()[
        "id"
    ]

    response = client.get(
        f"/api/documents/{document_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == document_id

    assert (
        data["original_filename"]
        == "detail-test.pdf"
    )


def test_documents_require_authentication(
    client,
):
    response = client.get(
        "/api/documents",
    )

    assert response.status_code == 401


def test_user_cannot_access_another_users_document(
    client,
):
    user_a_headers = create_auth_headers(
        client,
        name="User A",
        email="usera@example.com",
    )

    user_b_headers = create_auth_headers(
        client,
        name="User B",
        email="userb@example.com",
    )

    upload_response = upload_test_pdf(
        client,
        user_a_headers,
        filename="private.pdf",
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()[
        "id"
    ]

    response = client.get(
        f"/api/documents/{document_id}",
        headers=user_b_headers,
    )

    assert response.status_code == 404
    
def test_user_only_lists_their_own_documents(
    client,
):
    user_a_headers = create_auth_headers(
        client,
        name="List User A",
        email="lista@example.com",
    )

    user_b_headers = create_auth_headers(
        client,
        name="List User B",
        email="listb@example.com",
    )

    upload_response = upload_test_pdf(
        client,
        user_a_headers,
        filename="user-a-document.pdf",
    )

    assert upload_response.status_code == 201

    response = client.get(
        "/api/documents",
        headers=user_b_headers,
    )

    assert response.status_code == 200

    documents = response.json()

    assert documents == []
    
def test_delete_document(
    client,
    auth_headers,
):
    upload_response = upload_test_pdf(
        client,
        auth_headers,
        filename="delete-me.pdf",
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()[
        "id"
    ]

    delete_response = client.delete(
        f"/api/documents/{document_id}",
        headers=auth_headers,
    )

    assert delete_response.status_code == 200

    data = delete_response.json()

    assert (
        data["document_id"]
        == document_id
    )

    get_response = client.get(
        f"/api/documents/{document_id}",
        headers=auth_headers,
    )

    assert get_response.status_code == 404