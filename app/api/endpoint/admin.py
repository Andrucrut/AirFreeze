from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentAdmin, get_db
from app.db_crud.booking import booking_crud
from app.db_crud.flight import flight_crud
from app.db_crud.freeze import freeze_crud
from app.db_crud.user import user_crud
from app.schemas.booking import BookingListOut, BookingOut, BookingPatchIn
from app.schemas.flight import FlightCreateIn, FlightListOut, FlightOut, FlightPatchIn
from app.schemas.freeze import FreezeListOut, FreezeOut
from app.schemas.user import AdminUserPatchIn, UserListOut, UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


# --- Users ---


@router.get("/users", response_model=UserListOut)
async def admin_list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: CurrentAdmin,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> UserListOut:
    items, total = await user_crud.list_paginated(db, skip=skip, limit=limit)
    return UserListOut(
        items=[UserOut.model_validate(u) for u in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/users/{user_id}", response_model=UserOut)
async def admin_get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: CurrentAdmin,
) -> UserOut:
    user = await user_crud.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserOut.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserOut)
async def admin_patch_user(
    user_id: int,
    body: AdminUserPatchIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: CurrentAdmin,
) -> UserOut:
    if body.is_admin is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    user = await user_crud.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await user_crud.set_admin(db, user, is_admin=body.is_admin)
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


# --- Flights ---


@router.get("/flights", response_model=FlightListOut)
async def admin_list_flights(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: CurrentAdmin,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    from_city: Annotated[str | None, Query(max_length=128)] = None,
    to_city: Annotated[str | None, Query(max_length=128)] = None,
) -> FlightListOut:
    rows, total = await flight_crud.list_paginated(
        db, skip=skip, limit=limit, from_city=from_city, to_city=to_city
    )
    return FlightListOut(
        items=[FlightOut.model_validate(f) for f in rows],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("/flights", response_model=FlightOut, status_code=status.HTTP_201_CREATED)
async def admin_create_flight(
    body: FlightCreateIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: CurrentAdmin,
) -> FlightOut:
    if body.arrival_time <= body.departure_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="arrival_time must be after departure_time",
        )
    flight = await flight_crud.create(
        db,
        from_city=body.from_city,
        to_city=body.to_city,
        departure_time=body.departure_time,
        arrival_time=body.arrival_time,
        price=body.price,
        stops=body.stops,
    )
    await db.commit()
    await db.refresh(flight)
    return FlightOut.model_validate(flight)


@router.patch("/flights/{flight_id}", response_model=FlightOut)
async def admin_patch_flight(
    flight_id: int,
    body: FlightPatchIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: CurrentAdmin,
) -> FlightOut:
    if not body.model_dump(exclude_unset=True):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    flight = await flight_crud.get_by_id(db, flight_id)
    if flight is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found")
    dep = body.departure_time if body.departure_time is not None else flight.departure_time
    arr = body.arrival_time if body.arrival_time is not None else flight.arrival_time
    if arr <= dep:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="arrival_time must be after departure_time",
        )
    await flight_crud.update(
        db,
        flight,
        from_city=body.from_city,
        to_city=body.to_city,
        departure_time=body.departure_time,
        arrival_time=body.arrival_time,
        price=body.price,
        stops=body.stops,
    )
    await db.commit()
    await db.refresh(flight)
    return FlightOut.model_validate(flight)


@router.delete("/flights/{flight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_flight(
    flight_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: CurrentAdmin,
) -> None:
    flight = await flight_crud.get_by_id(db, flight_id)
    if flight is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found")
    await flight_crud.delete(db, flight)
    await db.commit()


# --- Freezes ---


@router.get("/freezes", response_model=FreezeListOut)
async def admin_list_freezes(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: CurrentAdmin,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    user_id: Annotated[int | None, Query()] = None,
) -> FreezeListOut:
    rows, total = await freeze_crud.list_paginated(db, skip=skip, limit=limit, user_id=user_id)
    return FreezeListOut(
        items=[FreezeOut.model_validate(r) for r in rows],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/freezes/{freeze_id}", response_model=FreezeOut)
async def admin_get_freeze(
    freeze_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: CurrentAdmin,
) -> FreezeOut:
    row = await freeze_crud.get_by_id(db, freeze_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Freeze not found")
    return FreezeOut.model_validate(row)


@router.delete("/freezes/{freeze_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_freeze(
    freeze_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: CurrentAdmin,
) -> None:
    row = await freeze_crud.get_by_id(db, freeze_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Freeze not found")
    await freeze_crud.delete(db, row)
    await db.commit()


# --- Bookings ---


@router.get("/bookings", response_model=BookingListOut)
async def admin_list_bookings(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: CurrentAdmin,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    user_id: Annotated[int | None, Query()] = None,
) -> BookingListOut:
    rows, total = await booking_crud.list_paginated(db, skip=skip, limit=limit, user_id=user_id)
    return BookingListOut(
        items=[BookingOut.model_validate(r) for r in rows],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/bookings/{booking_id}", response_model=BookingOut)
async def admin_get_booking(
    booking_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: CurrentAdmin,
) -> BookingOut:
    row = await booking_crud.get_by_id(db, booking_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return BookingOut.model_validate(row)


@router.patch("/bookings/{booking_id}", response_model=BookingOut)
async def admin_patch_booking(
    booking_id: int,
    body: BookingPatchIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: CurrentAdmin,
) -> BookingOut:
    row = await booking_crud.get_by_id(db, booking_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    await booking_crud.set_status(db, row, status=body.status)
    await db.commit()
    await db.refresh(row)
    return BookingOut.model_validate(row)


@router.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_booking(
    booking_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: CurrentAdmin,
) -> None:
    row = await booking_crud.get_by_id(db, booking_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    await booking_crud.delete(db, row)
    await db.commit()
