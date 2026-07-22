from datetime import date


def test_home_stats_defaults_for_new_account(client, register_user):
    headers, _ = register_user()
    resp = client.get("/api/home", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_applications"] == 0
    assert body["total_applied"] == 0
    assert body["response_rate"] is None
    assert body["interview_rate"] is None
    assert body["offer_rate"] is None
    assert body["weekly_goal_low"] == 5
    assert body["weekly_goal_high"] == 10
    assert body["due_follow_ups"] == []


def test_home_stats_reflect_applications(client, register_user):
    headers, _ = register_user()
    today = date.today().isoformat()
    client.post("/api/applications", json={"company": "A", "status": "Applied", "date_applied": today}, headers=headers)
    client.post("/api/applications", json={"company": "B", "status": "Interview", "date_applied": today}, headers=headers)
    client.post("/api/applications", json={"company": "C", "status": "Draft Ready"}, headers=headers)

    resp = client.get("/api/home", headers=headers)
    body = resp.json()
    assert body["total_applications"] == 3
    # Draft Ready does not count as sent; Applied and Interview do.
    assert body["total_applied"] == 2
    assert body["applied_this_week"] == 2
    assert body["funnel"]["Applied"] == 1
    assert body["funnel"]["Interview"] == 1
    assert body["funnel"]["Draft Ready"] == 1
    # response/interview rates are counted against applications actually sent (2), not the total (3).
    assert body["interview_rate"] == 0.5
    assert body["response_rate"] == 0.5
    assert body["offer_rate"] == 0.0


def test_home_stats_due_follow_ups(client, register_user):
    headers, _ = register_user()
    today = date.today().isoformat()
    client.post("/api/applications", json={"company": "A", "follow_up_date": today}, headers=headers)
    client.post("/api/applications", json={"company": "B"}, headers=headers)

    resp = client.get("/api/home", headers=headers)
    body = resp.json()
    assert len(body["due_follow_ups"]) == 1
    assert body["due_follow_ups"][0]["company"] == "A"


def test_home_stats_use_account_weekly_goal(client, register_user):
    headers, _ = register_user()
    client.patch("/api/settings", json={"weekly_goal_low": 3, "weekly_goal_high": 7}, headers=headers)
    resp = client.get("/api/home", headers=headers)
    body = resp.json()
    assert body["weekly_goal_low"] == 3
    assert body["weekly_goal_high"] == 7


def test_home_stats_require_auth(client):
    resp = client.get("/api/home")
    assert resp.status_code == 401
