from sqlalchemy import Column, Integer, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base, sessionmaker
from config import Config


class TableBase:
    pk = Column(Integer, primary_key=True, autoincrement=True)

    @declared_attr
    def __tablename__(self) -> str:
        name = self.__name__.lower()
        if name.endswith('y'):
            return name[:-1] + 'ies'
        if name.endswith('s'):
            return name
        return name + 's'

    @classmethod
    async def create(cls, pk, **kwargs):
        async for session in db.get_session():
            obj = cls(pk=pk, **kwargs)
            session.add(obj)
            try:
                await session.commit()
                return obj
            except Exception:
                await session.rollback()
                raise

    @classmethod
    async def get(cls, pk):
        async for session in db.get_session():
            query = select(cls).where(cls.pk == pk)
            result = await session.execute(query)
            return result.scalars().first()

    @classmethod
    async def update(cls, pk, **kwargs):
        async for session in db.get_session():
            query = (
                update(cls)
                .where(cls.pk == pk)
                .values(**kwargs)
                .execution_options(synchronize_session="fetch")
            )
            try:
                await session.execute(query)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    @classmethod
    async def delete(cls, pk):
        async for session in db.get_session():
            query = delete(cls).where(cls.pk == pk)
            try:
                await session.execute(query)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise

    @classmethod
    async def get_all(cls):
        async for session in db.get_session():
            query = select(cls)
            result = await session.execute(query)
            return result.scalars().all()



Base = declarative_base(cls=TableBase)


class AsyncDatabaseSession:
    def __init__(self):
        self._engine = None
        self._sessionmaker = None

    async def init(self):
        self._engine = create_async_engine(
            Config.DB_CONFIG,
            echo=False,               
            future=True,
            pool_pre_ping=True,       
            pool_size=10,             
            max_overflow=20,           
            pool_recycle=1800,        
            pool_timeout=30,          
        )
        self._sessionmaker = sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

    async def get_session(self) -> AsyncSession: # type: ignore
        async with self._sessionmaker() as session:
            yield session

    async def create_all(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_all(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            
    


db = AsyncDatabaseSession()
