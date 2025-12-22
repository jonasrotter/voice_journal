"""User service layer."""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from api.users.models import User
from api.users.schemas import UserCreate, UserUpdate
from api.auth.utils import get_password_hash


def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user."""
    password_hash = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        password_hash=password_hash
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, user_data: UserUpdate) -> User:
    """Update an existing user."""
    update_data = user_data.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    """Permanently delete a user and all associated data."""
    db.delete(user)
    db.commit()
