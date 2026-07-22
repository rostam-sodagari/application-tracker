def test_meta_requires_auth(client):
    resp = client.get("/api/meta")
    assert resp.status_code == 401


def test_meta_lists_application_statuses(client, register_user):
    headers, _ = register_user()
    resp = client.get("/api/meta", headers=headers)
    assert resp.status_code == 200
    statuses = resp.json()["application_statuses"]
    assert "Draft Ready" in statuses
    assert "Applied" in statuses
    assert "Offer" in statuses


def test_public_config_is_unauthenticated(client):
    resp = client.get("/api/public-config")
    assert resp.status_code == 200
    assert resp.json() == {"backend_mode": "local"}
