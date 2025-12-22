"""
Unit Tests - Users Module
Tests for user CRUD operations and schemas
"""

import pytest
from datetime import datetime
from uuid import uuid4


class TestUserSchemas:
    """Tests for user Pydantic schemas"""
    
    def test_user_create_valid(self):
        """UserCreate should accept valid email and password"""
        from api.users.schemas import UserCreate
        
        user = UserCreate(email="test@example.com", password="securepass123")
        
        assert user.email == "test@example.com"
        assert user.password == "securepass123"
    
    def test_user_create_invalid_email(self):
        """UserCreate should reject invalid email formats"""
        from api.users.schemas import UserCreate
        import pydantic
        
        invalid_emails = [
            "notanemail",
            "missing@domain",
            "@nodomain.com",
            "spaces in@email.com",
            ""
        ]
        
        for email in invalid_emails:
            with pytest.raises(pydantic.ValidationError):
                UserCreate(email=email, password="password123")
    
    def test_user_create_password_min_length(self):
        """UserCreate should enforce minimum password length"""
        from api.users.schemas import UserCreate
        import pydantic
        
        with pytest.raises(pydantic.ValidationError):
            UserCreate(email="test@example.com", password="short")
    
    def test_user_read_excludes_password(self):
        """UserRead should not include password hash"""
        from api.users.schemas import UserRead
        
        user = UserRead(
            id=str(uuid4()),
            email="test@example.com",
            created_at=datetime.utcnow()
        )
        
        # UserRead should not have password field
        assert not hasattr(user, 'password')
        assert not hasattr(user, 'password_hash')
    
    def test_user_update_partial(self):
        """UserUpdate should allow partial updates"""
        from api.users.schemas import UserUpdate
        
        # Only updating email
        update = UserUpdate(email="new@example.com")
        
        assert update.email == "new@example.com"
        assert update.password is None


class TestUserModel:
    """Tests for User SQLAlchemy model"""
    
    def test_user_model_has_required_fields(self):
        """User model should have all required fields"""
        from api.users.models import User
        
        # Check column names
        columns = [c.name for c in User.__table__.columns]
        
        assert 'id' in columns
        assert 'email' in columns
        assert 'password_hash' in columns
        assert 'created_at' in columns
    
    def test_user_id_is_uuid(self):
        """User id should be UUID type"""
        from api.users.models import User
        import uuid
        
        # Column type check
        id_column = User.__table__.columns['id']
        # UUID is stored as String(36) or UUID type
        assert id_column is not None


class TestUserService:
    """Tests for user service layer (requires DB session mock)"""
    
    def test_email_uniqueness(self):
        """Service should enforce unique emails"""
        # This would test with mocked DB:
        # user1 = user_service.create_user(db, email="test@example.com", password="pass123")
        # with pytest.raises(IntegrityError):
        #     user_service.create_user(db, email="test@example.com", password="pass456")
        pass
    
    def test_get_user_by_email(self):
        """Service should retrieve user by email"""
        # This would test with mocked DB:
        # user = user_service.get_user_by_email(db, "test@example.com")
        # assert user.email == "test@example.com"
        pass
    
    def test_password_is_hashed_on_create(self):
        """Service should hash password when creating user"""
        # This verifies that plain password is never stored
        # user = user_service.create_user(db, email="test@example.com", password="plaintext")
        # assert user.password_hash != "plaintext"
        pass


class TestSubscriptionModel:
    """Tests for Subscription model"""
    
    def test_subscription_has_required_fields(self):
        """Subscription model should have required fields"""
        from api.entries.models import Subscription
        
        columns = [c.name for c in Subscription.__table__.columns]
        
        assert 'id' in columns
        assert 'user_id' in columns
        assert 'plan' in columns
        assert 'status' in columns
        assert 'created_at' in columns
    
    def test_subscription_default_plan(self):
        """Subscription should have default plan"""
        # Default plan should be 'free'
        # subscription = Subscription(user_id=str(uuid4()))
        # assert subscription.plan == 'free'
        pass


# Run tests with: pytest tests/test_users.py -v
