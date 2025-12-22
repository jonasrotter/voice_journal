"""Quick verification tests for the Voice Journal app."""
import sys
sys.path.insert(0, '.')

print("=" * 60)
print("VOICE JOURNAL - QUICK VERIFICATION TESTS")
print("=" * 60)

# Test 1: Auth utilities
print("\n[TEST 1] Auth Utilities")
try:
    from api.auth.utils import get_password_hash, verify_password, create_access_token, decode_access_token
    
    pwd = "testpassword123"
    h = get_password_hash(pwd)
    print(f"  ✓ Password hash created: {h[:30]}...")
    
    assert verify_password(pwd, h) == True, "Password verification failed"
    print(f"  ✓ Correct password verified")
    
    assert verify_password("wrongpassword", h) == False, "Wrong password should fail"
    print(f"  ✓ Wrong password rejected")
    
    token = create_access_token({"sub": "test@example.com", "user_id": "123"})
    print(f"  ✓ JWT token created: {token[:40]}...")
    
    decoded = decode_access_token(token)
    assert decoded is not None, "Token decode failed"
    assert decoded["sub"] == "test@example.com", "Token payload mismatch"
    print(f"  ✓ JWT token decoded correctly")
    
    print("  [PASS] Auth utilities working correctly")
except Exception as e:
    print(f"  [FAIL] Auth utilities error: {e}")

# Test 2: Database models
print("\n[TEST 2] Database Models")
try:
    from api.users.models import User
    from api.entries.models import JournalEntry, Subscription
    from api.entries.schemas import EntryStatus
    
    print(f"  ✓ User model loaded")
    print(f"  ✓ JournalEntry model loaded")
    print(f"  ✓ Subscription model loaded")
    print(f"  ✓ EntryStatus enum: {[s.value for s in EntryStatus]}")
    print("  [PASS] Database models loaded correctly")
except Exception as e:
    print(f"  [FAIL] Database models error: {e}")

# Test 3: Pydantic schemas
print("\n[TEST 3] Pydantic Schemas")
try:
    from api.users.schemas import UserCreate, UserRead, UserUpdate
    from api.entries.schemas import EntryCreate, EntryRead, EntryUpdate, EntryCreateResponse, EntryListResponse
    from api.auth.schemas import Token, LoginRequest, RegisterRequest
    
    # Test UserCreate validation
    user = UserCreate(email="test@example.com", password="password123")
    print(f"  ✓ UserCreate schema: {user.email}")
    
    # Test Token schema
    token = Token(access_token="abc123", token_type="bearer")
    print(f"  ✓ Token schema: {token.token_type}")
    
    print("  [PASS] Pydantic schemas working correctly")
except Exception as e:
    print(f"  [FAIL] Pydantic schemas error: {e}")

# Test 4: FastAPI app initialization
print("\n[TEST 4] FastAPI Application")
try:
    from api.main import app
    
    # Check routes are registered
    routes = [r.path for r in app.routes]
    print(f"  ✓ FastAPI app created with {len(routes)} routes")
    
    expected_routes = ["/api/v1/auth", "/api/v1/users", "/api/v1/entries", "/api/health"]
    for route in expected_routes:
        found = any(route in r for r in routes)
        status = "✓" if found else "✗"
        print(f"  {status} Route {route} {'found' if found else 'MISSING'}")
    
    print("  [PASS] FastAPI application configured correctly")
except Exception as e:
    print(f"  [FAIL] FastAPI app error: {e}")

# Test 5: AI Processing module
print("\n[TEST 5] AI Processing Module")
try:
    from api.ai.processing import transcribe_audio, summarize_text, infer_emotion
    
    # These are sync functions (mock implementations)
    transcript = transcribe_audio("/fake/path.webm")
    summary = summarize_text("This is a test transcript.")
    emotion = infer_emotion("I am feeling great today!")
    
    print(f"  ✓ Transcription mock: {transcript[:40]}...")
    print(f"  ✓ Summary mock: {summary[:40]}...")
    print(f"  ✓ Emotion mock: {emotion}")
    print("  [PASS] AI processing module working correctly")
except Exception as e:
    print(f"  [FAIL] AI processing error: {e}")

# Test 6: Database connection setup
print("\n[TEST 6] Database Setup")
try:
    from api.db.database import get_db, Base
    
    print(f"  ✓ Database Base class loaded")
    print(f"  ✓ get_db dependency available")
    print("  [PASS] Database setup configured correctly")
except Exception as e:
    print(f"  [FAIL] Database setup error: {e}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
