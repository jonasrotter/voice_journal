"""Integration tests for the Voice Journal API."""
import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from uuid import uuid4

print("=" * 60)
print("VOICE JOURNAL - API INTEGRATION TESTS")
print("=" * 60)

# Setup test client with in-memory SQLite
import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from api.main import app
from api.db.database import Base, engine

# Create tables
Base.metadata.create_all(bind=engine)

client = TestClient(app)

# Test counters
passed = 0
failed = 0

def test(name, condition, msg=""):
    global passed, failed
    if condition:
        print(f"  ✓ {name}")
        passed += 1
    else:
        print(f"  ✗ {name} - {msg}")
        failed += 1

# Test 1: Health Check
print("\n[TEST 1] Health Check")
response = client.get("/api/health")
test("GET /api/health returns 200", response.status_code == 200)
test("Response has status field", response.json().get("status") == "healthy")

# Test 2: User Registration
print("\n[TEST 2] User Registration")
test_email = f"test_{uuid4().hex[:8]}@example.com"
test_password = "testpassword123"

response = client.post("/api/v1/auth/register", json={
    "email": test_email,
    "password": test_password
})
test("POST /auth/register returns 201", response.status_code == 201, f"Got {response.status_code}: {response.text}")

if response.status_code == 201:
    user_data = response.json()
    test("Response has id", "id" in user_data)
    test("Response has email", user_data.get("email") == test_email)
    test("Response excludes password", "password" not in user_data and "password_hash" not in user_data)

# Test 3: Duplicate Registration
print("\n[TEST 3] Duplicate Registration")
response = client.post("/api/v1/auth/register", json={
    "email": test_email,
    "password": "differentpassword"
})
test("Duplicate email rejected", response.status_code == 400, f"Got {response.status_code}")

# Test 4: User Login
print("\n[TEST 4] User Login")
response = client.post("/api/v1/auth/login", json={
    "email": test_email,
    "password": test_password
})
test("POST /auth/login returns 200", response.status_code == 200, f"Got {response.status_code}: {response.text}")

auth_token = None
if response.status_code == 200:
    token_data = response.json()
    test("Response has access_token", "access_token" in token_data)
    test("Token type is bearer", token_data.get("token_type") == "bearer")
    auth_token = token_data.get("access_token")

# Test 5: Invalid Login
print("\n[TEST 5] Invalid Login")
response = client.post("/api/v1/auth/login", json={
    "email": test_email,
    "password": "wrongpassword"
})
test("Wrong password rejected", response.status_code == 401, f"Got {response.status_code}")

response = client.post("/api/v1/auth/login", json={
    "email": "nonexistent@example.com",
    "password": "anypassword"
})
test("Unknown email rejected", response.status_code == 401, f"Got {response.status_code}")

# Test 6: Get Current User (Authenticated)
print("\n[TEST 6] Get Current User")
if auth_token:
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/api/v1/users/me", headers=headers)
    test("GET /users/me returns 200", response.status_code == 200, f"Got {response.status_code}: {response.text}")
    
    if response.status_code == 200:
        user = response.json()
        test("Response has correct email", user.get("email") == test_email)

# Test 7: Unauthorized Access
print("\n[TEST 7] Unauthorized Access")
response = client.get("/api/v1/users/me")
test("No token returns 401", response.status_code == 401, f"Got {response.status_code}")

response = client.get("/api/v1/users/me", headers={"Authorization": "Bearer invalid-token"})
test("Invalid token returns 401", response.status_code == 401, f"Got {response.status_code}")

# Test 8: Get Entries (Empty)
print("\n[TEST 8] Get Entries (Empty List)")
if auth_token:
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/api/v1/entries", headers=headers)
    test("GET /entries returns 200", response.status_code == 200, f"Got {response.status_code}: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        test("Response has entries array", "entries" in data)
        test("Response has total count", "total" in data)

# Test 9: Upload Entry
print("\n[TEST 9] Upload Audio Entry")
if auth_token:
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Create fake audio file
    audio_content = b"RIFF" + b"\x00" * 100  # Minimal WAV-like header
    
    response = client.post(
        "/api/v1/entries",
        headers=headers,
        files={"audio": ("test.webm", audio_content, "audio/webm")}
    )
    test("POST /entries returns 201", response.status_code == 201, f"Got {response.status_code}: {response.text}")
    
    entry_id = None
    if response.status_code == 201:
        entry_data = response.json()
        test("Response has id", "id" in entry_data)
        test("Response has audio_url", "audio_url" in entry_data)
        entry_id = entry_data.get("id")

# Test 10: Get Single Entry
print("\n[TEST 10] Get Single Entry")
if auth_token and entry_id:
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get(f"/api/v1/entries/{entry_id}", headers=headers)
    test("GET /entries/{id} returns 200", response.status_code == 200, f"Got {response.status_code}: {response.text}")
    
    if response.status_code == 200:
        entry = response.json()
        test("Entry has correct id", str(entry.get("id")) == entry_id)
        test("Entry has status", "status" in entry)

# Test 11: Entry Not Found
print("\n[TEST 11] Entry Not Found")
if auth_token:
    headers = {"Authorization": f"Bearer {auth_token}"}
    fake_id = str(uuid4())
    response = client.get(f"/api/v1/entries/{fake_id}", headers=headers)
    test("Unknown entry returns 404", response.status_code == 404, f"Got {response.status_code}")

# Test 12: Delete Entry
print("\n[TEST 12] Delete Entry")
if auth_token and entry_id:
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.delete(f"/api/v1/entries/{entry_id}", headers=headers)
    test("DELETE /entries/{id} returns 204", response.status_code == 204, f"Got {response.status_code}: {response.text}")
    
    # Verify deletion
    response = client.get(f"/api/v1/entries/{entry_id}", headers=headers)
    test("Deleted entry returns 404", response.status_code == 404, f"Got {response.status_code}")

# Test 13: User Isolation
print("\n[TEST 13] User Isolation")
# Create second user
user2_email = f"user2_{uuid4().hex[:8]}@example.com"
response = client.post("/api/v1/auth/register", json={
    "email": user2_email,
    "password": "password123"
})

if response.status_code == 201:
    # Login as user2
    response = client.post("/api/v1/auth/login", json={
        "email": user2_email,
        "password": "password123"
    })
    
    if response.status_code == 200:
        user2_token = response.json().get("access_token")
        headers2 = {"Authorization": f"Bearer {user2_token}"}
        
        # User2 should see empty entries (not user1's entries)
        response = client.get("/api/v1/entries", headers=headers2)
        test("User2 sees own entries only", response.status_code == 200 and response.json().get("total", -1) == 0)

# Summary
print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 60)

# Cleanup
import os
if os.path.exists("test.db"):
    os.remove("test.db")

if failed == 0:
    print("\n✅ ALL TESTS PASSED!")
else:
    print(f"\n❌ {failed} TEST(S) FAILED")
    sys.exit(1)
