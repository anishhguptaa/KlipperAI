from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from src.shared.core.database import get_db
from src.api.modules.auth.schemas import UserResponse
from .service import UserService


router = APIRouter(prefix="/user", tags=["User"])


@router.get(
    "/details",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user details",
    description="Return basic details for the currently authenticated user",
)
async def get_user_details(
    request: Request,
    db: Session = Depends(get_db),
):
    return UserService.get_user_details(db=db, user_id=request.state.user_id)
