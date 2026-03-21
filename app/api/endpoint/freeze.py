from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.db_crud.flight import flight_crud
from app.db_crud.freeze import freeze_crud
from app.schemas.freeze import FreezeCreateIn, FreezeOut

router = APIRouter(prefix="/freeze", tags=["freeze"])


@router.get("/my", response_model=list[FreezeOut])
async def list_my_freezes(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> list[FreezeOut]:
    rows = await freeze_crud.list_for_user(db, current_user.id)
    return [FreezeOut.model_validate(r) for r in rows]


@router.get("/{freeze_id}", response_model=FreezeOut)
async def get_my_freeze(
    freeze_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> FreezeOut:
    row = await freeze_crud.get_by_id(db, freeze_id)
    if row is None or row.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Freeze not found")
    return FreezeOut.model_validate(row)


@router.delete("/{freeze_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_freeze(
    freeze_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> None:
    row = await freeze_crud.get_by_id(db, freeze_id)
    if row is None or row.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Freeze not found")
    await freeze_crud.delete(db, row)
    await db.commit()


@router.post("", response_model=FreezeOut, status_code=status.HTTP_201_CREATED)
async def create_freeze(
    body: FreezeCreateIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> FreezeOut:
    flight = await flight_crud.get_by_id(db, body.flight_id)
    if flight is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found")
    now = datetime.now(timezone.utc)
    if flight.departure_time <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot freeze price for a flight that has already departed",
        )
    freeze = await freeze_crud.create_for_flight(
        db,
        user_id=current_user.id,
        flight_id=flight.id,
        price_at_freeze=float(flight.price),
    )
    await db.commit()
    await db.refresh(freeze)
    return FreezeOut.model_validate(freeze)
