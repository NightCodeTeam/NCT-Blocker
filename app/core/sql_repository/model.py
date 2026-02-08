from abc import ABC
from typing import Type, AsyncGenerator, Tuple, List

from sqlalchemy import text, select, delete, exists, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .classes import T
from .exeptions import SessionNotFound, GetMultiple


AddManyObjects = Tuple[T, ...] | List[T]


class Repository(ABC):
    """Улучшенная версия базового репозитория для работы с базой данных"""
    table_name: str

    def __init__(self, model: Type[T], session: AsyncSession, relationships: List[str] | Tuple[str] | None = None):
        self.model = model
        self.table_name = model.__tablename__
        self.relationships = relationships

        self.session = session

    async def __get_object_from_db(
        self,
        _filter: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
        order_by_field: str | None = None,
        load_relations: bool = True,
    ) -> tuple[T]:
        query = select(self.model)
        if load_relations and self.relationships:
            for relationship in self.relationships:
                if hasattr(self.model, relationship):
                    query = query.options(selectinload(getattr(self.model, relationship)))

        if _filter is not None:
            query = query.filter(text(_filter))
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        if order_by_field:
            query = query.order_by(text(order_by_field))

        try:
            return tuple((await self.session.execute(query)).scalars().all())
        except AttributeError:
            raise SessionNotFound()

    async def get(
        self,
        _filter: str,
        load_relations: bool = True,
    ) -> T | None:
        objs = await self.__get_object_from_db(_filter=_filter, load_relations=load_relations)
        if len(objs) > 1:
            raise GetMultiple(self.model, len(objs))
        elif len(objs) == 0:
            return None
        return objs[0]

    async def some(
        self,
        _filter: str,
        offset: int | None = None,
        limit: int | None = None,
        order_by_field: str | None = None,
        load_relations: bool = True,
    ) -> tuple[T, ...]:
        return await self.__get_object_from_db(
            _filter=_filter,
            offset=offset,
            limit=limit,
            order_by_field=order_by_field,
            load_relations=load_relations
        )

    async def __add(self, model: T, commit: bool = False) -> bool:
        try:
            self.session.add(model)
            if commit:
                await self.session.commit()
            return True
        except AttributeError as e:
            raise SessionNotFound()
            return False

    async def add(
        self,
        model: T,
        commit: bool = False,
    ) -> bool:
        return await self.__add(model, commit)

    async def add_many(
        self,
        objs: AddManyObjects,
        commit: bool = False
    ) -> bool:
        try:
            self.session.add_all(objs)
            if commit:
                await self.session.commit()
            return True
        except AttributeError as e:
            raise SessionNotFound()

    async def delete(self, obj: T, commit: bool = False) -> bool:
        try:
            await self.session.delete(obj)
            if commit:
                await self.session.commit()
            return True
        except AttributeError as e:
            raise SessionNotFound()
            return False

    async def all(
        self,
        skip: int | None = None,
        limit: int | None = None,
        order_by_field: str | None = None,
        load_relations: bool = True,
    ) -> tuple[T, ...]:
        return await self.__get_object_from_db(
            offset=skip,
            limit=limit,
            order_by_field=order_by_field,
            load_relations=load_relations,
        )

    async def clear_table(self, commit: bool = False) -> bool:
        try:
            await self.session.execute(delete(self.model))
            if commit:
                await self.session.commit()
            return True
        except AttributeError as e:
            raise SessionNotFound()

    async def _exists(self, _filter: str) -> bool:
        try:
            return bool(await self.session.scalar(select(exists().select_from(self.model).where(text(_filter)))))
        except AttributeError as e:
            raise SessionNotFound()

    async def count(self) -> int:
        try:
            return (await self.session.execute(select(func.count()).select_from(self.model))).scalar()
        except AttributeError as e:
            raise SessionNotFound()

    async def all_gen(
        self,
        load_relations: bool = False, skip: int = 0,
        search_field: str = 'id'
    ) -> AsyncGenerator[Type[T]]:
        for i in range(skip, await self.count()):
            yield await self.get(
                f'{self.model.__tablename__}.{search_field}={i}',
                load_relations=load_relations,
            )

    async def _pagination(
        self,
        _filter: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
        order_by_field: str | None = None,
        load_relations: bool = False,
    ) -> tuple[T, ...]:
        return await self.some(
            _filter=_filter,
            offset=skip,
            limit=limit,
            order_by_field=order_by_field,
            load_relations=load_relations,
        )
