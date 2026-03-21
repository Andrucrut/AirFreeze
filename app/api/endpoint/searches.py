from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.db_crud.search_history import search_history_crud
from app.schemas.search_history import SearchHistoryListOut, SearchHistoryOut

router = APIRouter(prefix="/searches", tags=["searches"])


@router.get("/my", response_model=SearchHistoryListOut)
async def list_my_search_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> SearchHistoryListOut:
    rows, total = await search_history_crud.list_for_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return SearchHistoryListOut(
        items=[SearchHistoryOut.model_validate(r) for r in rows],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_search_entry(
    entry_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> None:
    ok = await search_history_crud.delete_for_user(db, user_id=current_user.id, entry_id=entry_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search history entry not found")
    await db.commit()
