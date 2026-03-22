from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDRepository
from app.models.payment_method import PaymentMethod


class PaymentMethodCRUD(CRUDRepository[PaymentMethod]):
    def __init__(self) -> None:
        super().__init__(PaymentMethod)

    async def create_card(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        last_four: str,
        holder_name: str,
        label: str = "Карта",
    ) -> PaymentMethod:
        row = PaymentMethod(
            user_id=user_id,
            label=label,
            last_four=last_four,
            holder_name=holder_name.strip(),
            created_at=datetime.now(timezone.utc),
        )
        session.add(row)
        await session.flush()
        await session.refresh(row)
        return row

    async def list_for_user(self, session: AsyncSession, user_id: int) -> list[PaymentMethod]:
        result = await session.execute(
            select(PaymentMethod)
            .where(PaymentMethod.user_id == user_id)
            .order_by(PaymentMethod.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_owned(self, session: AsyncSession, pm_id: int, user_id: int) -> PaymentMethod | None:
        result = await session.execute(
            select(PaymentMethod).where(
                PaymentMethod.id == pm_id,
                PaymentMethod.user_id == user_id,
            )
        )
        return result.scalars().first()

    async def delete(self, session: AsyncSession, row: PaymentMethod) -> None:
        await session.delete(row)
        await session.flush()


payment_method_crud = PaymentMethodCRUD()
