from datetime import datetime

from sqlalchemy import Column, Integer, String, update, delete, Date, BigInteger
from sqlalchemy.future import select

from aiobot.database import Base, db


class Users(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, unique=True)
    full_name = Column(String(30))
    phone_number = Column(String(30))
    lang = Column(String(2))
    status = Column(String, default="user")
    created_at = Column(Date, default=datetime.now)

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}: pk={self.pk}, user_id={self.user_id}, "
            f"full_name={self.full_name}, lang={self.lang}, status={self.status}>"
        )

    @classmethod
    async def create(cls, user_id, **kwargs):
        user = cls(user_id=user_id, **kwargs)
        async for session in db.get_session():
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


    @classmethod
    async def get(cls, user_id):
        async for session in db.get_session():
            query = select(cls).where(cls.user_id == user_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()


    @classmethod
    async def get_all(cls):
        async for session in db.get_session():
            query = select(cls)
            result = await session.execute(query)
            return result.scalars().all()


    @classmethod
    async def update(cls, user_id, **kwargs):
        async for session in db.get_session():
            query = (
                update(cls)
                .where(cls.user_id == user_id)
                .values(**kwargs)
                .execution_options(synchronize_session="fetch")
            )
            await session.execute(query)
            await session.commit()


    @classmethod
    async def delete(cls, user_id):
        async for session in db.get_session():
            query = delete(cls).where(cls.user_id == user_id)
            await session.execute(query)
            await session.commit()
        return True


    @classmethod
    async def get_language(cls, user_id):
        user = await cls.get(user_id)
        if user and hasattr(user, "lang"):
            return user.lang
        return "ru"
