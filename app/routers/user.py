# coding=utf-8
from typing import Union

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from app.schemas import User
from app.security.token_service import get_current_active_user
from sqlalchemy.orm import Session
from app.services import user_service, operation_service

from app.dependencies import get_db

router = APIRouter(
    prefix="/users",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)


@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.post("/")
async def create_user(
    user: User,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    new_user = user_service.create_user(user=user, db=db)
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"停用产品 {new_user.username} {new_user.role}", db
    )
    return JSONResponse(content={"user": new_user, "success": True})
