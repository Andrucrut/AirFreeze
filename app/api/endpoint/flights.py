from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import OptionalUser, get_db
from app.db_crud.flight import flight_crud
from app.db_crud.search_history import search_history_crud
from app.schemas.flight import FlightListOut, FlightOut

router = APIRouter(prefix="/flights", tags=["flights"])


@router.get("", response_model=FlightListOut)
async def list_flights_catalog(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    from_city: Annotated[str | None, Query(max_length=128)] = None,
    to_city: Annotated[str | None, Query(max_length=128)] = None,
) -> FlightListOut:
    rows, total = await flight_crud.list_paginated(
        db, skip=skip, limit=limit, from_city=from_city, to_city=to_city
    )
    await db.commit()
    return FlightListOut(
        items=[FlightOut.model_validate(f) for f in rows],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/search", response_model=list[FlightOut])
async def search_flights(
    db: Annotated[AsyncSession, Depends(get_db)],
    optional_user: OptionalUser,
    from_city: Annotated[str, Query(min_length=1, max_length=128)],
    to_city: Annotated[str, Query(min_length=1, max_length=128)],
    date: Annotated[date, Query(description="Flight departure date (UTC day bucket)")],
    passengers: Annotated[int, Query(ge=1, le=9)] = 1,
    sort_by: Annotated[
        Literal["price", "duration", "departure_time"],
        Query(description="Sort results"),
    ] = "departure_time",
    sort_order: Annotated[Literal["asc", "desc"], Query()] = "asc",
    max_price: Annotated[float | None, Query(gt=0, description="Only flights up to this price")] = None,
    max_stops: Annotated[int | None, Query(ge=0, description="Maximum number of stops")] = None,
) -> list[FlightOut]:
    flights = await flight_crud.search(
        db,
        from_city=from_city,
        to_city=to_city,
        flight_date=date,
        passengers=passengers,
        sort_by=sort_by,
        sort_order=sort_order,
        max_price=max_price,
        max_stops=max_stops,
    )
    if optional_user is not None:
        await search_history_crud.create_entry(
            db,
            user_id=optional_user.id,
            from_city=from_city,
            to_city=to_city,
            flight_date=date,
            passengers=passengers,
            sort_by=sort_by,
            sort_order=sort_order,
            max_price=max_price,
            max_stops=max_stops,
            result_count=len(flights),
        )
        await db.commit()
    else:
        await db.commit()
    return [FlightOut.model_validate(f) for f in flights]


@router.get("/{flight_id}", response_model=FlightOut)
async def get_flight(
    flight_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FlightOut:
    flight = await flight_crud.get_by_id(db, flight_id)
    if flight is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found")
    await db.commit()
    return FlightOut.model_validate(flight)
