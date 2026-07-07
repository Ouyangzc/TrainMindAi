"""Generic CRUD 基类。"""

from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base


class BaseRepository[ModelT: Base]:
    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    async def get(self, id: int) -> ModelT | None:
        return await self.session.get(self.model, id)

    async def find(
        self,
        *filters: Any,
        order_by: Any | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ModelT]:
        stmt = select(self.model).where(*filters)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, *filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model).where(*filters)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def add(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def add_all(self, instances: list[ModelT]) -> list[ModelT]:
        self.session.add_all(instances)
        await self.session.flush()
        return instances

    async def update(self, instance: ModelT, **values: Any) -> ModelT:
        for field, value in values.items():
            setattr(instance, field, value)
        await self.session.flush()
        return instance

    async def delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)
        await self.session.flush()

    def _build_select(self, *filters: Any, order_by: Any | None = None) -> Select:
        stmt = select(self.model).where(*filters)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        return stmt
