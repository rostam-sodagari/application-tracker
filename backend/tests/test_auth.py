def test_register_creates_account_and_returns_token(client):
    resp = client.post("/api/auth/register", json={"email": "new@example.com", "password": "password123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "new@example.com"
    # No SMTP configured in the test environment, so the account is verified immediately.
    assert body["email_verified"] is True
    assert body["token"]


def test_register_rejects_invalid_email(client):
    resp = client.post("/api/auth/register", json={"email": "not-an-email", "password": "password123"})
    assert resp.status_code == 400


def test_register_rejects_short_password(client):
    resp = client.post("/api/auth/register", json={"email": "a@example.com", "password": "short"})
    assert resp.status_code == 400


def test_register_rejects_duplicate_email(client):
    client.post("/api/auth/register", json={"email": "dup@example.com", "password": "password123"})
    resp = client.post("/api/auth/register", json={"email": "dup@example.com", "password": "password123"})
    assert resp.status_code == 409


def test_login_with_correct_credentials(client):
    client.post("/api/auth/register", json={"email": "login@example.com", "password": "password123"})
    resp = client.post("/api/auth/login", json={"email": "login@example.com", "password": "password123"})
    assert resp.status_code == 200
    assert resp.json()["token"]


def test_login_with_wrong_password_fails(client):
    client.post("/api/auth/register", json={"email": "login2@example.com", "password": "password123"})
    resp = client.post("/api/auth/login", json={"email": "login2@example.com", "password": "wrongpassword"})
    assert resp.status_code == 401


def test_login_with_unknown_email_fails(client):
    resp = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "password123"})
    assert resp.status_code == 401


def test_login_rate_limited_after_five_failures(client):
    client.post("/api/auth/register", json={"email": "limited@example.com", "password": "password123"})
    for _ in range(5):
        client.post("/api/auth/login", json={"email": "limited@example.com", "password": "wrong"})
    resp = client.post("/api/auth/login", json={"email": "limited@example.com", "password": "wrong"})
    assert resp.status_code == 429


def test_rate_limit_tracking_does_not_accumulate_for_clean_logins(client):
    from app.auth_providers import local_auth

    client.post("/api/auth/register", json={"email": "clean@example.com", "password": "password123"})
    client.post("/api/auth/login", json={"email": "clean@example.com", "password": "password123"})
    # A successful login still passes through the rate limiter; it must not leave a permanent
    # entry behind for a client IP with no outstanding failed attempts.
    assert local_auth._login_attempts == {}


def test_whoami_requires_token(client):
    resp = client.get("/api/auth/whoami")
    assert resp.status_code == 401


def test_whoami_rejects_garbage_token(client):
    resp = client.get("/api/auth/whoami", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_whoami_returns_current_account(client, register_user):
    headers, email = register_user()
    resp = client.get("/api/auth/whoami", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"email": email, "email_verified": True}


def test_resend_verification_when_already_verified(client, register_user):
    headers, _ = register_user()
    resp = client.post("/api/auth/resend-verification", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "already_verified": True}


def test_verify_email_flow_with_smtp_configured(client, monkeypatch):
    from app import email_sender

    sent = {}
    monkeypatch.setattr(email_sender, "smtp_configured", lambda: True)
    monkeypatch.setattr(
        email_sender, "send_verification_email", lambda to_email, verify_url: sent.update(to=to_email, url=verify_url)
    )

    resp = client.post("/api/auth/register", json={"email": "verify@example.com", "password": "password123"})
    body = resp.json()
    assert body["email_verified"] is False
    assert sent["to"] == "verify@example.com"

    token = sent["url"].split("token=", 1)[1]
    confirm = client.get(f"/api/auth/verify-email?token={token}")
    assert confirm.status_code == 200
    assert confirm.json()["email"] == "verify@example.com"

    headers = {"Authorization": f"Bearer {body['token']}"}
    who = client.get("/api/auth/whoami", headers=headers)
    assert who.json()["email_verified"] is True


def test_resend_verification_requires_smtp_configured(client, monkeypatch, register_user):
    from app import email_sender

    monkeypatch.setattr(email_sender, "smtp_configured", lambda: True)
    resp = client.post("/api/auth/register", json={"email": "unverified@example.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {resp.json()['token']}"}

    monkeypatch.setattr(email_sender, "smtp_configured", lambda: False)
    resend = client.post("/api/auth/resend-verification", headers=headers)
    assert resend.status_code == 400


def test_verify_email_rejects_bad_token(client):
    resp = client.get("/api/auth/verify-email?token=not-a-real-token")
    assert resp.status_code == 400
