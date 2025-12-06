import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def restore_activities():
    """Backup and restore the in-memory activities between tests."""
    orig = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(orig)


def test_get_activities():
    client = TestClient(app)
    r = client.get("/activities")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_and_unregister_flow():
    client = TestClient(app)
    activity = "Chess Club"
    email = "test.student@example.com"

    # Ensure not present
    r = client.get("/activities")
    assert email not in r.json()[activity]["participants"]

    # Sign up
    r = client.post(f"/activities/{quote(activity)}/signup", params={"email": email})
    assert r.status_code == 200

    # Now should be present
    r = client.get("/activities")
    assert email in r.json()[activity]["participants"]

    # Unregister
    r = client.delete(f"/activities/{quote(activity)}/unregister", params={"email": email})
    assert r.status_code == 200

    # Back to not present
    r = client.get("/activities")
    assert email not in r.json()[activity]["participants"]


def test_duplicate_signup_and_bad_unregister():
    client = TestClient(app)
    activity = "Programming Class"
    email = "dup.student@example.com"

    # First signup succeeds
    r = client.post(f"/activities/{quote(activity)}/signup", params={"email": email})
    assert r.status_code == 200

    # Second signup should fail with 400
    r = client.post(f"/activities/{quote(activity)}/signup", params={"email": email})
    assert r.status_code == 400

    # Unregistering a non-registered user should return 404
    r = client.delete(f"/activities/{quote(activity)}/unregister", params={"email": "not.real@example.com"})
    assert r.status_code == 404
