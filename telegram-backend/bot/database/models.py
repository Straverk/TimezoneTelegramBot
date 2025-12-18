from typing import List
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


engine = create_async_engine("sqlite+aiosqlite:////data/database.sqlite")
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)

    # timezones_id: Mapped[List["Timezone"]] = mapped_column()
    timezones: Mapped[List["Timezone"]] = relationship(
        back_populates=None,
        lazy="selectin",
        cascade="all, delete-orphan"
    )


class Timezone(Base):
    __tablename__ = "timezones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    description: Mapped[str] = mapped_column(String(32))
    tzone: Mapped[int] = mapped_column(Integer)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    # user: Mapped["User"] = relationship(back_populates="timezones")


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
