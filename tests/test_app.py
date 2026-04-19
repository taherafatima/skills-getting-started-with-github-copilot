"""
Tests for the Mergington High School API using FastAPI TestClient.
Tests follow the AAA (Arrange-Act-Assert) pattern.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestRootEndpoint:
    def test_get_root_redirects_to_static_index(self):
        # Arrange: No special setup needed
        
        # Act: Make GET request to root without following redirects
        response = client.get("/", follow_redirects=False)
        
        # Assert: Should redirect to static index
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    def test_get_activities_returns_all_activities(self):
        # Arrange: Activities are pre-loaded in app
        
        # Act: Fetch activities
        response = client.get("/activities")
        
        # Assert: Returns 200 and contains expected activities
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        
        # Verify structure of activity data
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignupEndpoint:
    def test_signup_successful_for_valid_activity_and_email(self):
        # Arrange: Use an activity with available spots
        email = "newstudent@mergington.edu"
        activity_name = "Basketball Team"  # Starts with empty participants
        
        # Act: Sign up for activity
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert: Returns success and adds participant
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email in result["message"]
        
        # Verify participant was added
        response2 = client.get("/activities")
        activity = response2.json()[activity_name]
        assert email in activity["participants"]
    
    def test_signup_fails_for_nonexistent_activity(self):
        # Arrange: Use invalid activity name
        email = "student@mergington.edu"
        invalid_activity = "Nonexistent Club"
        
        # Act: Attempt signup
        response = client.post(f"/activities/{invalid_activity}/signup?email={email}")
        
        # Assert: Returns 404 with error message
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert "Activity not found" in result["detail"]
    
    def test_signup_fails_for_duplicate_registration(self):
        # Arrange: Sign up once first
        email = "duplicatestudent@mergington.edu"
        activity_name = "Soccer Club"
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Act: Try to sign up again
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert: Returns 400 with duplicate error
        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "already signed up" in result["detail"]
    
    def test_signup_fails_when_activity_is_full(self):
        # Arrange: Fill up an activity
        activity_name = "Chess Club"  # Max 12 participants
        base_email = "fulltest"
        
        # Fill to max (already has 2, add 10 more)
        for i in range(10):
            email = f"{base_email}{i}@mergington.edu"
            client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Act: Try to add one more
        response = client.post(f"/activities/{activity_name}/signup?email=overflow@mergington.edu")
        
        # Assert: Returns 400 with full error
        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "Activity is full" in result["detail"]


class TestUnregisterEndpoint:
    def test_unregister_successful_for_registered_participant(self):
        # Arrange: Sign up first
        email = "unregistertest@mergington.edu"
        activity_name = "Drama Club"
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Act: Unregister
        response = client.delete(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert: Returns success and removes participant
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "Unregistered" in result["message"]
        
        # Verify participant was removed
        response2 = client.get("/activities")
        activity = response2.json()[activity_name]
        assert email not in activity["participants"]
    
    def test_unregister_fails_for_nonexistent_activity(self):
        # Arrange: Use invalid activity
        email = "student@mergington.edu"
        invalid_activity = "Fake Club"
        
        # Act: Attempt unregister
        response = client.delete(f"/activities/{invalid_activity}/signup?email={email}")
        
        # Assert: Returns 404
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert "Activity not found" in result["detail"]
    
    def test_unregister_fails_for_unregistered_participant(self):
        # Arrange: Use email not in activity
        email = "notregistered@mergington.edu"
        activity_name = "Debate Club"
        
        # Act: Attempt unregister
        response = client.delete(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert: Returns 400
        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "Not registered" in result["detail"]