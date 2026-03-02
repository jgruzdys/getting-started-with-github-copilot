import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

# keep an immutable snapshot of the starting activities so each test can
# restore the in‑memory database
_initial_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the global `activities` dict before every test."""
    activities.clear()
    activities.update(copy.deepcopy(_initial_activities))
    yield
    # no special teardown required


@pytest.fixture
def client():
    return TestClient(app)


def test_root_redirect(client):
    # Arrange
    # (no special setup required)

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    # Arrange
    # (initial activities already in place)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    # ensure one of the known activities is present
    assert "Chess Club" in data


def test_signup_for_existing_activity(client):
    # Arrange
    activity = "Chess Club"
    email = "new@mergington.edu"
    assert email not in activities[activity]["participants"]

    # Act
    response = client.post(
        f"/activities/{activity}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert email in activities[activity]["participants"]
    assert "Signed up" in response.json().get("message", "")


def test_signup_duplicate(client):
    # Arrange
    activity = "Chess Club"
    email = activities[activity]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_nonexistent_activity(client):
    # Arrange
    activity = "Nonexistent"

    # Act
    response = client.post(
        f"/activities/{activity}/signup", params={"email": "foo@bar.com"}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant(client):
    # Arrange
    activity = "Chess Club"
    email = activities[activity]["participants"][0]
    assert email in activities[activity]["participants"]

    # Act
    response = client.delete(
        f"/activities/{activity}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert email not in activities[activity]["participants"]
    assert "Removed" in response.json().get("message", "")


def test_remove_nonparticipant(client):
    # Arrange
    activity = "Chess Club"
    email = "nobody@mergington.edu"
    assert email not in activities[activity]["participants"]

    # Act
    response = client.delete(
        f"/activities/{activity}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student not registered for this activity"


def test_remove_nonexistent_activity(client):
    # Arrange
    activity = "NotThere"

    # Act
    response = client.delete(
        f"/activities/{activity}/participants", params={"email": "foo@bar.com"}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
