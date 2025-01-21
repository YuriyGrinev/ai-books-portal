from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .....domain.entities.base import Entity
from ..models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)
EntityType = TypeVar("EntityType", bound=Entity)


class BaseRepository(Generic[ModelType, EntityType]):
    """Base repository implementation"""

    def __init__(self, session: AsyncSession, model: Type[ModelType], entity: Type[EntityType]):
        self.session = session
        self.model = model
        self.entity = entity

    async def create(self, entity_data: EntityType) -> EntityType:
        """Create a new entity"""
        db_obj = self.model(**entity_data.model_dump(exclude={"id", "created_at", "updated_at"}))
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return self.entity.model_validate(db_obj)

    async def get(self, id: UUID) -> Optional[EntityType]:
        """Get entity by id"""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj is None:
            return None
        return self.entity.model_validate(db_obj)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[EntityType]:
        """Get all entities with pagination"""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return [self.entity.model_validate(obj) for obj in result.scalars().all()]

    async def update(self, id: UUID, entity_data: EntityType) -> Optional[EntityType]:
        """Update entity"""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj is None:
            return None

        obj_data = entity_data.model_dump(exclude={"id", "created_at", "updated_at"}, exclude_unset=True)
        for field, value in obj_data.items():
            setattr(db_obj, field, value)

        await self.session.flush()
        await self.session.refresh(db_obj)
        return self.entity.model_validate(db_obj)

    async def delete(self, id: UUID) -> bool:
        """Delete entity"""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj is None:
            return False

        await self.session.delete(db_obj)
        await self.session.flush()
        return True 