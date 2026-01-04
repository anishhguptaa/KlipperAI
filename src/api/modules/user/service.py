from sqlalchemy.orm import Session
from typing import Optional
from fastapi import HTTPException, status
from src.api.modules.auth.schemas import UserResponse
from src.core.logger import get_logger
from src.models.DbModels import User

logger = get_logger(__name__)

class UserService:
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_details(db: Session, user_id: int) -> UserResponse:
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        logger.info(f"User details fetched for user_id={user.id}")
        return UserResponse.model_validate(user)
