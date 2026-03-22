from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.core.card_validation import (
    last_four_digits,
    luhn_valid,
    normalize_card_number,
    validate_cvc,
)
from app.db_crud.payment_method import payment_method_crud
from app.schemas.payment_method import PaymentMethodCreateIn, PaymentMethodOut

router = APIRouter(prefix="/payment-methods", tags=["payment-methods"])


@router.get("/my", response_model=list[PaymentMethodOut])
async def list_my_payment_methods(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> list[PaymentMethodOut]:
    rows = await payment_method_crud.list_for_user(db, current_user.id)
    return [PaymentMethodOut.model_validate(r) for r in rows]


@router.post("", response_model=PaymentMethodOut, status_code=status.HTTP_201_CREATED)
async def add_payment_method(
    body: PaymentMethodCreateIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> PaymentMethodOut:
    try:
        num = normalize_card_number(body.card_number)
        if not luhn_valid(num):
            raise ValueError("Invalid card number")
        validate_cvc(body.cvc)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    row = await payment_method_crud.create_card(
        db,
        user_id=current_user.id,
        last_four=last_four_digits(num),
        holder_name=body.card_holder.strip(),
    )
    await db.commit()
    await db.refresh(row)
    return PaymentMethodOut.model_validate(row)


@router.delete("/{payment_method_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_method(
    payment_method_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> None:
    row = await payment_method_crud.get_owned(db, payment_method_id, current_user.id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
    await payment_method_crud.delete(db, row)
    await db.commit()
