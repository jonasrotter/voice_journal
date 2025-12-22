"""
Contract Tests - API Schema Validation
Verifies that API responses match expected schemas
"""

import pytest
from uuid import uuid4
from datetime import datetime


# Note: 'client' fixture comes from conftest.py


class TestUserContractSchema:
    """Contract tests for User schema"""
    
    REQUIRED_FIELDS = ["id", "email", "created_at"]
    FORBIDDEN_FIELDS = ["password", "password_hash"]
    
    def test_register_response_schema(self, client):
        """POST /auth/register response should match UserRead schema"""
        email = f"contract_{uuid4().hex[:8]}@example.com"
        
        response = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "password123"
        })
        
        data = response.json()
        
        # Verify required fields present
        for field in self.REQUIRED_FIELDS:
            assert field in data, f"Missing required field: {field}"
        
        # Verify forbidden fields absent
        for field in self.FORBIDDEN_FIELDS:
            assert field not in data, f"Forbidden field present: {field}"
        
        # Verify field types
        assert isinstance(data["id"], str)
        assert isinstance(data["email"], str)
        assert isinstance(data["created_at"], str)
    
    def test_get_me_response_schema(self, client):
        """GET /users/me response should match UserRead schema"""
        # Setup
        email = f"contract_{uuid4().hex[:8]}@example.com"
        client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
        token = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
        
        response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        
        # Verify schema compliance
        for field in self.REQUIRED_FIELDS:
            assert field in data, f"Missing required field: {field}"
        
        for field in self.FORBIDDEN_FIELDS:
            assert field not in data, f"Forbidden field present: {field}"


class TestTokenContractSchema:
    """Contract tests for Token schema"""
    
    def test_login_response_schema(self, client):
        """POST /auth/login response should match Token schema"""
        # Setup
        email = f"contract_{uuid4().hex[:8]}@example.com"
        client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
        
        response = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
        data = response.json()
        
        # Required fields
        assert "access_token" in data
        assert "token_type" in data
        
        # Type validation
        assert isinstance(data["access_token"], str)
        assert isinstance(data["token_type"], str)
        assert data["token_type"] == "bearer"
        
        # Token format (JWT has 3 parts)
        parts = data["access_token"].split(".")
        assert len(parts) == 3


class TestEntryContractSchema:
    """Contract tests for Entry schema"""
    
    ENTRY_REQUIRED_FIELDS = ["id", "user_id", "audio_url", "status", "created_at"]
    ENTRY_OPTIONAL_FIELDS = ["transcript", "summary", "emotion"]
    VALID_STATUSES = ["uploaded", "processing", "processed", "failed"]
    
    def test_upload_response_schema(self, client):
        """POST /entries response should match EntryCreateResponse schema"""
        # Setup
        email = f"contract_{uuid4().hex[:8]}@example.com"
        client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
        token = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
        
        response = client.post(
            "/api/v1/entries",
            headers={"Authorization": f"Bearer {token}"},
            files={"audio": ("test.webm", b"WEBM" + bytes(100), "audio/webm")}
        )
        data = response.json()
        
        # Required fields for create response
        assert "id" in data
        assert "audio_url" in data
        assert "status" in data
        
        # Type validation
        assert isinstance(data["id"], str)
        assert isinstance(data["audio_url"], str)
        assert isinstance(data["status"], str)
    
    def test_get_entry_response_schema(self, client):
        """GET /entries/{id} response should match EntryRead schema"""
        # Setup
        email = f"contract_{uuid4().hex[:8]}@example.com"
        client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
        token = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create entry
        upload_response = client.post(
            "/api/v1/entries",
            headers=headers,
            files={"audio": ("test.webm", b"WEBM" + bytes(100), "audio/webm")}
        )
        entry_id = upload_response.json()["id"]
        
        # Get entry
        response = client.get(f"/api/v1/entries/{entry_id}", headers=headers)
        data = response.json()
        
        # Required fields
        for field in self.ENTRY_REQUIRED_FIELDS:
            assert field in data, f"Missing required field: {field}"
        
        # Status validation
        assert data["status"] in self.VALID_STATUSES
        
        # Type validation
        assert isinstance(data["id"], str)
        assert isinstance(data["user_id"], str)
        assert isinstance(data["audio_url"], str)
        assert isinstance(data["status"], str)
    
    def test_list_entries_response_schema(self, client):
        """GET /entries response should match EntryListResponse schema"""
        # Setup
        email = f"contract_{uuid4().hex[:8]}@example.com"
        client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
        token = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
        
        response = client.get("/api/v1/entries", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        
        # Required fields for list response
        assert "entries" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        
        # Type validation
        assert isinstance(data["entries"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["page"], int)
        assert isinstance(data["page_size"], int)
        
        # Validate each entry in list
        for entry in data["entries"]:
            for field in self.ENTRY_REQUIRED_FIELDS:
                assert field in entry


class TestErrorContractSchema:
    """Contract tests for error responses"""
    
    def test_validation_error_schema(self, client):
        """Validation errors should have standard format"""
        response = client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "x"
        })
        
        assert response.status_code == 422
        data = response.json()
        
        # FastAPI validation error format
        assert "detail" in data
    
    def test_auth_error_schema(self, client):
        """Auth errors should have detail field"""
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        data = response.json()
        
        assert "detail" in data
        assert isinstance(data["detail"], str)
    
    def test_not_found_error_schema(self, client):
        """Not found errors should have detail field"""
        # Setup
        email = f"contract_{uuid4().hex[:8]}@example.com"
        client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
        token = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
        
        response = client.get(
            f"/api/v1/entries/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
        data = response.json()
        
        assert "detail" in data


# Run tests with: pytest tests/test_contracts.py -v
