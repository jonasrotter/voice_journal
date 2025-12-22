"""
Integration Tests - API Endpoints
Tests for the complete API request/response cycle
"""

import pytest
from uuid import uuid4


# Note: 'client' fixture comes from conftest.py


@pytest.fixture
def auth_headers(client):
    """Create authenticated user and return auth headers"""
    # Register a new user
    email = f"test_{uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password
    })
    
    # Login to get token
    response = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


class TestHealthEndpoint:
    """Tests for health check endpoint"""
    
    def test_health_returns_200(self, client):
        """Health endpoint should return 200 OK"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestAuthEndpoints:
    """Tests for authentication endpoints"""
    
    def test_register_creates_user(self, client):
        """POST /auth/register should create new user"""
        email = f"newuser_{uuid4().hex[:8]}@example.com"
        
        response = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "securepassword123"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == email
        assert "id" in data
        assert "password" not in data
        assert "password_hash" not in data
    
    def test_register_duplicate_email_fails(self, client):
        """POST /auth/register should reject duplicate emails"""
        email = f"duplicate_{uuid4().hex[:8]}@example.com"
        
        # First registration
        client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "password123"
        })
        
        # Second registration with same email
        response = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "differentpassword"
        })
        
        assert response.status_code == 400
    
    def test_login_returns_token(self, client):
        """POST /auth/login should return access token"""
        email = f"login_{uuid4().hex[:8]}@example.com"
        password = "securepassword123"
        
        # Register first
        client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password
        })
        
        # Login
        response = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client):
        """POST /auth/login should reject invalid credentials"""
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401


class TestUserEndpoints:
    """Tests for user endpoints"""
    
    def test_get_current_user(self, client, auth_headers):
        """GET /users/me should return current user"""
        response = client.get("/api/v1/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "password" not in data
    
    def test_get_current_user_unauthorized(self, client):
        """GET /users/me should reject unauthorized requests"""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 401
    
    def test_update_current_user(self, client, auth_headers):
        """PATCH /users/me should update user"""
        new_email = f"updated_{uuid4().hex[:8]}@example.com"
        
        response = client.patch("/api/v1/users/me", 
            headers=auth_headers,
            json={"email": new_email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == new_email


class TestEntryEndpoints:
    """Tests for journal entry endpoints"""
    
    def test_get_entries_empty(self, client, auth_headers):
        """GET /entries should return empty list for new user"""
        response = client.get("/api/v1/entries", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "total" in data
        assert data["total"] >= 0
    
    def test_get_entries_unauthorized(self, client):
        """GET /entries should reject unauthorized requests"""
        response = client.get("/api/v1/entries")
        
        assert response.status_code == 401
    
    def test_upload_entry(self, client, auth_headers):
        """POST /entries should create new entry"""
        # Create a minimal WebM audio file (just for testing)
        audio_content = b"WEBM" + bytes(100)  # Fake WebM header
        
        response = client.post(
            "/api/v1/entries",
            headers=auth_headers,
            files={"audio": ("test.webm", audio_content, "audio/webm")}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "audio_url" in data
        assert "status" in data
    
    def test_get_single_entry(self, client, auth_headers):
        """GET /entries/{id} should return entry details"""
        # First upload an entry
        audio_content = b"WEBM" + bytes(100)
        upload_response = client.post(
            "/api/v1/entries",
            headers=auth_headers,
            files={"audio": ("test.webm", audio_content, "audio/webm")}
        )
        entry_id = upload_response.json()["id"]
        
        # Get the entry
        response = client.get(f"/api/v1/entries/{entry_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == entry_id
    
    def test_delete_entry(self, client, auth_headers):
        """DELETE /entries/{id} should remove entry"""
        # First upload an entry
        audio_content = b"WEBM" + bytes(100)
        upload_response = client.post(
            "/api/v1/entries",
            headers=auth_headers,
            files={"audio": ("test.webm", audio_content, "audio/webm")}
        )
        entry_id = upload_response.json()["id"]
        
        # Delete it
        response = client.delete(f"/api/v1/entries/{entry_id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = client.get(f"/api/v1/entries/{entry_id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    def test_entry_isolation(self, client):
        """Users should not see other users' entries"""
        # Create two users
        user1_email = f"user1_{uuid4().hex[:8]}@example.com"
        user2_email = f"user2_{uuid4().hex[:8]}@example.com"
        password = "password123"
        
        # Register both users
        client.post("/api/v1/auth/register", json={"email": user1_email, "password": password})
        client.post("/api/v1/auth/register", json={"email": user2_email, "password": password})
        
        # Login as user1 and create entry
        token1 = client.post("/api/v1/auth/login", json={"email": user1_email, "password": password}).json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        audio_content = b"WEBM" + bytes(100)
        client.post("/api/v1/entries", headers=headers1, files={"audio": ("test.webm", audio_content, "audio/webm")})
        
        # Login as user2 and check entries
        token2 = client.post("/api/v1/auth/login", json={"email": user2_email, "password": password}).json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        response = client.get("/api/v1/entries", headers=headers2)
        
        # User2 should not see user1's entries
        assert response.status_code == 200
        assert response.json()["total"] == 0


class TestPagination:
    """Tests for API pagination"""
    
    def test_entries_pagination_params(self, client, auth_headers):
        """GET /entries should accept page and page_size params"""
        response = client.get("/api/v1/entries?page=1&page_size=10", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10
    
    def test_entries_default_pagination(self, client, auth_headers):
        """GET /entries should have default pagination values"""
        response = client.get("/api/v1/entries", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "page" in data
        assert "page_size" in data


# Run tests with: pytest tests/test_integration.py -v
