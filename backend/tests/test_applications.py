def test_create_application_returns_full_record(client, register_user):
    headers, _ = register_user()
    resp = client.post("/api/applications", json={"company": "Acme", "role": "Engineer"}, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["company"] == "Acme"
    assert body["role"] == "Engineer"
    assert body["status"] == "Draft Ready"
    assert body["id"]


def test_create_application_with_new_fields(client, register_user):
    headers, _ = register_user()
    resp = client.post(
        "/api/applications",
        json={"company": "Acme", "salary_min": 50000, "salary_max": 60000, "location": "London", "remote_type": "Hybrid"},
        headers=headers,
    )
    body = resp.json()
    assert body["salary_min"] == 50000
    assert body["salary_max"] == 60000
    assert body["location"] == "London"
    assert body["remote_type"] == "Hybrid"


def test_list_applications_paginated_shape(client, register_user):
    headers, _ = register_user()
    for i in range(3):
        client.post("/api/applications", json={"company": f"Company {i}"}, headers=headers)
    resp = client.get("/api/applications", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3


def test_search_applications_by_keyword(client, register_user):
    headers, _ = register_user()
    client.post("/api/applications", json={"company": "Acme Corp", "role": "Backend"}, headers=headers)
    client.post("/api/applications", json={"company": "Other Co", "role": "Frontend"}, headers=headers)
    resp = client.get("/api/applications?keyword=Acme", headers=headers)
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["company"] == "Acme Corp"


def test_filter_applications_by_status(client, register_user):
    headers, _ = register_user()
    client.post("/api/applications", json={"company": "A", "status": "Applied"}, headers=headers)
    client.post("/api/applications", json={"company": "B", "status": "Draft Ready"}, headers=headers)
    resp = client.get("/api/applications?status=Applied", headers=headers)
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["company"] == "A"


def test_update_application(client, register_user):
    headers, _ = register_user()
    created = client.post("/api/applications", json={"company": "Acme"}, headers=headers).json()
    resp = client.patch(
        f"/api/applications/{created['id']}", json={"status": "Applied", "salary_min": 50000}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "Applied"
    assert resp.json()["salary_min"] == 50000


def test_update_application_rejects_invalid_status(client, register_user):
    headers, _ = register_user()
    created = client.post("/api/applications", json={"company": "Acme"}, headers=headers).json()
    resp = client.patch(f"/api/applications/{created['id']}", json={"status": "Not A Real Status"}, headers=headers)
    assert resp.status_code == 400


def test_delete_application(client, register_user):
    headers, _ = register_user()
    created = client.post("/api/applications", json={"company": "Acme"}, headers=headers).json()
    resp = client.delete(f"/api/applications/{created['id']}", headers=headers)
    assert resp.status_code == 204
    listing = client.get("/api/applications", headers=headers).json()
    assert listing["total"] == 0


def test_application_not_found_returns_404(client, register_user):
    headers, _ = register_user()
    resp = client.patch("/api/applications/does-not-exist", json={"status": "Applied"}, headers=headers)
    assert resp.status_code == 404
    resp = client.delete("/api/applications/does-not-exist", headers=headers)
    assert resp.status_code == 404


def test_applications_are_isolated_between_users(client, register_user):
    headers_a, _ = register_user("user-a@example.com")
    headers_b, _ = register_user("user-b@example.com")

    created = client.post("/api/applications", json={"company": "Only A's"}, headers=headers_a).json()

    listing_b = client.get("/api/applications", headers=headers_b).json()
    assert listing_b["total"] == 0

    resp = client.patch(f"/api/applications/{created['id']}", json={"status": "Applied"}, headers=headers_b)
    assert resp.status_code == 404
    resp = client.delete(f"/api/applications/{created['id']}", headers=headers_b)
    assert resp.status_code == 404

    listing_a = client.get("/api/applications", headers=headers_a).json()
    assert listing_a["total"] == 1


def test_applications_require_auth(client):
    resp = client.get("/api/applications")
    assert resp.status_code == 401
