def test_get_settings_returns_defaults(client, register_user):
    headers, _ = register_user()
    resp = client.get("/api/settings", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["weekly_goal_low"] == 5
    assert body["weekly_goal_high"] == 10


def test_update_settings(client, register_user):
    headers, _ = register_user()
    resp = client.patch("/api/settings", json={"weekly_goal_low": 2, "weekly_goal_high": 4}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["weekly_goal_low"] == 2
    assert body["weekly_goal_high"] == 4

    refetched = client.get("/api/settings", headers=headers)
    assert refetched.json()["weekly_goal_low"] == 2


def test_update_settings_partial(client, register_user):
    headers, _ = register_user()
    client.patch("/api/settings", json={"weekly_goal_low": 1, "weekly_goal_high": 2}, headers=headers)
    resp = client.patch("/api/settings", json={"weekly_goal_high": 9}, headers=headers)
    body = resp.json()
    assert body["weekly_goal_low"] == 1
    assert body["weekly_goal_high"] == 9


def test_settings_are_isolated_between_users(client, register_user):
    headers_a, _ = register_user("settings-a@example.com")
    headers_b, _ = register_user("settings-b@example.com")

    client.patch("/api/settings", json={"weekly_goal_low": 1, "weekly_goal_high": 2}, headers=headers_a)

    settings_b = client.get("/api/settings", headers=headers_b).json()
    assert settings_b["weekly_goal_low"] == 5
    assert settings_b["weekly_goal_high"] == 10


def test_settings_require_auth(client):
    resp = client.get("/api/settings")
    assert resp.status_code == 401
