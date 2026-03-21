from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.db_crud.user import user_crud
from app.models.user import User
from app.schemas.auth import LoginIn, RefreshIn, RegisterIn, TokenPairOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_pair(user: User) -> TokenPairOut:
    return TokenPairOut(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/register", response_model=TokenPairOut)
async def register(body: RegisterIn, db: Annotated[AsyncSession, Depends(get_db)]) -> TokenPairOut | JSONResponse:
    email_norm = str(body.email).lower().strip()
    existing = await user_crud.get_by_email(db, email_norm)
    if existing is not None:
        if verify_password(body.password, existing.password_hash):
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=_token_pair(existing).model_dump(),
            )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    is_admin = bool(
        settings.bootstrap_admin_email
        and email_norm == settings.bootstrap_admin_email.lower().strip()
    )
    try:
        user = await user_crud.create(
            db,
            email=email_norm,
            password_hash=hash_password(body.password),
            is_admin=is_admin,
        )
    except IntegrityError:
        await db.rollback()
        existing = await user_crud.get_by_email(db, email_norm)
        if existing is not None and verify_password(body.password, existing.password_hash):
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=_token_pair(existing).model_dump(),
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from None

    await db.commit()
    await db.refresh(user)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=_token_pair(user).model_dump(),
    )


@router.post("/login", response_model=TokenPairOut)
async def login(body: LoginIn, db: Annotated[AsyncSession, Depends(get_db)]) -> TokenPairOut:
    user = await user_crud.get_by_email(db, str(body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return _token_pair(user)


@router.post("/refresh", response_model=TokenPairOut)
async def refresh_token(body: RefreshIn, db: Annotated[AsyncSession, Depends(get_db)]) -> TokenPairOut:
    try:
        payload = decode_refresh_token(body.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    user_id = int(payload["sub"])
    user = await user_crud.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return _token_pair(user)
