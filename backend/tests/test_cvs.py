import io


def test_upload_list_and_open_cv(client, register_user):
    headers, _ = register_user()
    file_content = b"%PDF-1.4 fake pdf content"
    resp = client.post(
        "/api/cvs",
        headers=headers,
        files={"file": ("resume.pdf", io.BytesIO(file_content), "application/pdf")},
        data={"company": "Acme"},
    )
    assert resp.status_code == 201
    cv = resp.json()
    assert cv["file_name"] == "resume.pdf"
    assert cv["company"] == "Acme"

    listing = client.get("/api/cvs", headers=headers)
    assert len(listing.json()) == 1

    opened = client.get(f"/cvs/open/{cv['file_id']}", headers=headers)
    assert opened.status_code == 200
    assert opened.content == file_content


def test_update_cv_company(client, register_user):
    headers, _ = register_user()
    resp = client.post(
        "/api/cvs", headers=headers, files={"file": ("resume.pdf", io.BytesIO(b"content"), "application/pdf")}
    )
    cv = resp.json()
    updated = client.patch(f"/api/cvs/{cv['id']}", json={"company": "New Co"}, headers=headers)
    assert updated.json()["company"] == "New Co"


def test_update_missing_cv_returns_404(client, register_user):
    headers, _ = register_user()
    resp = client.patch("/api/cvs/does-not-exist", json={"company": "New Co"}, headers=headers)
    assert resp.status_code == 404


def test_delete_cv_removes_file(client, register_user):
    headers, _ = register_user()
    resp = client.post(
        "/api/cvs", headers=headers, files={"file": ("resume.pdf", io.BytesIO(b"content"), "application/pdf")}
    )
    cv = resp.json()
    deleted = client.delete(f"/api/cvs/{cv['id']}", headers=headers)
    assert deleted.status_code == 204

    listing = client.get("/api/cvs", headers=headers)
    assert listing.json() == []

    opened = client.get(f"/cvs/open/{cv['file_id']}", headers=headers)
    assert opened.status_code == 404


def test_cvs_are_isolated_between_users(client, register_user):
    headers_a, _ = register_user("cv-a@example.com")
    headers_b, _ = register_user("cv-b@example.com")

    resp = client.post(
        "/api/cvs", headers=headers_a, files={"file": ("resume.pdf", io.BytesIO(b"content"), "application/pdf")}
    )
    cv = resp.json()

    listing_b = client.get("/api/cvs", headers=headers_b)
    assert listing_b.json() == []

    opened_b = client.get(f"/cvs/open/{cv['file_id']}", headers=headers_b)
    assert opened_b.status_code == 404

    deleted_b = client.delete(f"/api/cvs/{cv['id']}", headers=headers_b)
    assert deleted_b.status_code == 404

    # user A's CV is unaffected
    listing_a = client.get("/api/cvs", headers=headers_a)
    assert len(listing_a.json()) == 1
