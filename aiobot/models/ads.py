from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, update, delete, BigInteger, Float
from sqlalchemy.future import select

from aiobot.database import Base, db


class Ads(Base):
    __tablename__ = "ads"
    user_id = Column(BigInteger, ForeignKey('users.user_id'))
    title = Column(String)
    price = Column(Float)
    size = Column(String)
    category = Column(String, nullable=True)
    condition = Column(String)
    defect_info = Column(String, nullable=True)
    photos = Column(String)
    status = Column(String, default='pending')
    admin_message_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    @classmethod
    async def create(cls, user_id, title, price, size, category, condition, defect_info, photos, status='pending'):
        ad = cls(
            user_id=user_id,
            title=title,
            price=price,
            size=size,
            category=category,
            condition=condition,
            defect_info=defect_info,
            photos=photos,
            status=status
        )
        async for session in db.get_session():
            session.add(ad)
            await session.commit()
            await session.refresh(ad)
        return ad

    @classmethod
    async def get(cls, ad_id):
        async for session in db.get_session():
            query = select(cls).where(cls.pk == ad_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def update_status(cls, ad_id, status):
        async for session in db.get_session():
            query = (
                update(cls)
                .where(cls.pk == ad_id)
                .values(status=status)
                .execution_options(synchronize_session="fetch")
            )
            await session.execute(query)
            await session.commit()

    @classmethod
    async def update_admin_message_id(cls, ad_id, message_id):
        async for session in db.get_session():
            query = (
                update(cls)
                .where(cls.pk == ad_id)
                .values(admin_message_id=message_id)
                .execution_options(synchronize_session="fetch")
            )
            await session.execute(query)
            await session.commit()

    @classmethod
    async def delete(cls, ad_id):
        async for session in db.get_session():
            query = delete(cls).where(cls.pk == ad_id)
            await session.execute(query)
            await session.commit()
        return True
