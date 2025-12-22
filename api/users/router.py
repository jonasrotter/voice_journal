"""User router."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.db import get_db
from api.auth.dependencies import get_current_user
from api.users.models import User
from api.users.schemas import UserRead, UserUpdate
from api.users import service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserRead:
    """Get current user's profile."""
    return current_user


@router.patch("/me", response_model=UserRead)
def update_current_user(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserRead:
    """Update current user's profile."""
    if user_data.email:
        existing = service.get_user_by_email(db, user_data.email)
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    return service.update_user(db, current_user, user_data)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """Permanently delete current user and all associated data (GDPR)."""
    service.delete_user(db, current_user)
