"""Covers the pure, network-free parts of app/stores/appwrite_store.py. The functions that call
Appwrite's TablesDB or Storage services are exercised manually against a live project instead, since
faking Appwrite's API convincingly would test the fake more than the code.
"""

from types import SimpleNamespace

from app.stores import appwrite_store as store


def test_owner_permissions_grants_read_update_delete_to_user():
    perms = store._owner_permissions("user-123")
    assert len(perms) == 3
    assert any("read" in p for p in perms)
    assert any("update" in p for p in perms)
    assert any("delete" in p for p in perms)
    assert all("user-123" in p for p in perms)


def test_row_to_application_maps_all_fields():
    row = SimpleNamespace(
        id="app-1",
        data={
            "company": "Acme", "role": "Engineer", "source": "LinkedIn", "job_url": "https://example.com",
            "cv_file_id": "cv-1", "cover_letter_file_id": None, "date_applied": "2026-07-01",
            "status": "Applied", "follow_up_date": None, "notes": "note",
            "salary_min": 50000, "salary_max": 60000, "location": "London", "remote_type": "Hybrid",
        },
        createdat="2026-07-01T00:00:00.000Z",
        updatedat="2026-07-02T00:00:00.000Z",
    )
    result = store._row_to_application(row)
    assert result["id"] == "app-1"
    assert result["company"] == "Acme"
    assert result["salary_min"] == 50000
    assert result["location"] == "London"
    assert result["created_at"] == "2026-07-01T00:00:00.000Z"
    assert result["updated_at"] == "2026-07-02T00:00:00.000Z"


def test_row_to_cv_version_maps_all_fields():
    row = SimpleNamespace(
        id="cv-1",
        data={"file_id": "file-1", "file_name": "resume.pdf", "company": "Acme"},
        createdat="2026-07-01T00:00:00.000Z",
    )
    result = store._row_to_cv_version(row)
    assert result == {
        "id": "cv-1",
        "file_id": "file-1",
        "file_name": "resume.pdf",
        "company": "Acme",
        "created_at": "2026-07-01T00:00:00.000Z",
    }
