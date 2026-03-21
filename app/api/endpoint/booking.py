from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.db_crud.booking import booking_crud
from app.db_crud.flight import flight_crud
from app.schemas.booking import BookingCreateIn, BookingOut, BookingUserCancelIn

router = APIRouter(prefix="/booking", tags=["booking"])


@router.get("/my", response_model=list[BookingOut])
async def list_my_bookings(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> list[BookingOut]:
    rows = await booking_crud.list_for_user(db, current_user.id)
    return [BookingOut.model_validate(r) for r in rows]


@router.get("/{booking_id}", response_model=BookingOut)
async def get_my_booking(
    booking_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> BookingOut:
    row = await booking_crud.get_by_id(db, booking_id)
    if row is None or row.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return BookingOut.model_validate(row)


@router.patch("/{booking_id}", response_model=BookingOut)
async def patch_my_booking(
    booking_id: int,
    body: BookingUserCancelIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> BookingOut:
    row = await booking_crud.get_by_id(db, booking_id)
    if row is None or row.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if row.status != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only confirmed bookings can be cancelled",
        )
    await booking_crud.set_status(db, row, status=body.status)
    await db.commit()
    await db.refresh(row)
    return BookingOut.model_validate(row)


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def create_booking(
    body: BookingCreateIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> BookingOut:
    flight = await flight_crud.get_by_id(db, body.flight_id)
    if flight is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found")
    now = datetime.now(timezone.utc)
    if flight.departure_time <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book a flight that has already departed",
        )
    booking, _price = await booking_crud.create_for_flight(db, user_id=current_user.id, flight=flight)
    await db.commit()
    await db.refresh(booking)
    return BookingOut.model_validate(booking)
