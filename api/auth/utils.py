"""Authentication utilities."""
import hashlib
import hmac
import base64
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from api.config import settings


def get_password_hash(password: str) -> str:
    """Hash a password using PBKDF2-SHA256."""
    salt = base64.b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest()[:16]).decode()
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt.encode(),
        100000
    )
    return f"{salt}${base64.b64encode(password_hash).decode()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        salt, stored_hash = hashed_password.split('$')
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode(),
            salt.encode(),
            100000
        )
        return hmac.compare_digest(
            base64.b64encode(password_hash).decode(),
            stored_hash
        )
    except (ValueError, AttributeError):
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = time.time() + expires_delta.total_seconds()
    else:
        expire = time.time() + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    
    to_encode.update({"exp": int(expire), "iat": int(time.time())})
    
    # Create JWT manually (no external dependencies)
    header = {"alg": settings.ALGORITHM, "typ": "JWT"}
    
    header_b64 = base64.urlsafe_b64encode(
        json.dumps(header, separators=(',', ':')).encode()
    ).rstrip(b'=').decode()
    
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(to_encode, separators=(',', ':')).encode()
    ).rstrip(b'=').decode()
    
    message = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
    
    return f"{message}.{signature_b64}"


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT access token."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        header_b64, payload_b64, signature_b64 = parts
        
        # Verify signature
        message = f"{header_b64}.{payload_b64}"
        expected_signature = hmac.new(
            settings.SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        
        # Add padding for base64 decoding
        signature_b64_padded = signature_b64 + '=' * (4 - len(signature_b64) % 4)
        actual_signature = base64.urlsafe_b64decode(signature_b64_padded)
        
        if not hmac.compare_digest(expected_signature, actual_signature):
            return None
        
        # Decode payload
        payload_b64_padded = payload_b64 + '=' * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64_padded))
        
        # Check expiration
        if payload.get("exp", 0) < time.time():
            return None
        
        return payload
    except Exception:
        return None
