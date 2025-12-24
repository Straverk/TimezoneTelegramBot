from typing import List
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, select
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from zoneinfo import available_timezones


engine = create_async_engine("sqlite+aiosqlite:////data/database.sqlite")
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)

    default_timezone: Mapped[str] = mapped_column(
        ForeignKey("timezones.iana"), nullable=True)

    """
    timezones: Mapped[List["UserTimezone"]] = relationship(
        back_populates=None,
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    """


class Timezone(Base):
    __tablename__ = "timezones"

    iana: Mapped[str] = mapped_column(String(64), primary_key=True)


class UserTimezone(Base):
    __tablename__ = "user_timezones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    description: Mapped[str] = mapped_column(String(32))
    iana: Mapped[str] = mapped_column(ForeignKey("timezones.iana"))

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Initialization
        zones = set(sorted(available_timezones()))

        result = await conn.execute(
            select(Timezone.iana)
        )
        db_zones = {row[0] for row in result.all()}

        missing = zones - db_zones
        if not missing:
            return

        async with async_session() as session:
            session.add_all(
                Timezone(iana=zone) for zone in missing
            )
            await session.commit()
