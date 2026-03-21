from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.core.security import hash_password, verify_password
from app.db_crud.user import user_crud
from app.schemas.user import UserMePasswordIn, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def read_me(current_user: CurrentUser) -> UserOut:
    return UserOut.model_validate(current_user)


@router.patch("/me/password", response_model=UserOut)
async def change_my_password(
    body: UserMePasswordIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> UserOut:
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    await user_crud.set_password_hash(db, current_user, password_hash=hash_password(body.new_password))
    await db.commit()
    await db.refresh(current_user)
    return UserOut.model_validate(current_user)
