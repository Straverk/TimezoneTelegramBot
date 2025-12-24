from typing import Any, Tuple, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert
from database.models import async_session
from database.models import User, Timezone, UserTimezone


def __get_user_select(chat_id):
    return select(User).where(User.chat_id == chat_id)


async def __get_user(session: AsyncSession, chat_id: int) -> User | None:
    return (await session.scalars(__get_user_select(chat_id))).first()


async def __get_or_add_user(session: AsyncSession, chat_id: int) -> User:
    user = await __get_user(session, chat_id)

    if user is None:
        user = User(chat_id=chat_id)
        session.add(user)
        await session.flush()

    return user


async def __get_timezone(session: AsyncSession, timezone_id: int):
    return await session.scalar(select(UserTimezone).where(UserTimezone.id == timezone_id))


async def get_user(chad_id: int) -> User | None:
    async with async_session() as session:
        return await __get_user(session, chad_id)


async def add_timezone(chat_id: int, data):
    async with async_session() as session:
        user = await __get_or_add_user(session, chat_id)

        iana = f"{data["region"]}/{data["city"]}"
        await session.execute(insert(UserTimezone).values(
            user_id=user.id,
            iana=iana,
            description=data["description"]
        ))

        if user.default_timezone == None:
            user.default_timezone = iana

        await session.commit()


async def get_timezone(timezone_id: int) -> UserTimezone | None:
    async with async_session() as session:
        return await __get_timezone(session, timezone_id)


async def get_timezones(chat_id: int) -> Tuple[UserTimezone]:
    async with async_session() as session:
        result = await session.execute(
            select(
                UserTimezone.description, UserTimezone.iana, UserTimezone.id
            )
            .join(User, User.id == UserTimezone.user_id)
            .where(User.chat_id == chat_id)
        )

        return tuple(result.all())


async def remove_timezone(chat_id: int, timezone_id: int) -> Dict | None:
    async with async_session() as session:
        user = await __get_user(session, chat_id)

        if user is None:
            return None

        result = await session.execute(
            delete(UserTimezone)
            .where(UserTimezone.id == timezone_id)
            .returning(
                UserTimezone.id,
                UserTimezone.description,
                UserTimezone.iana
            )
        )

        timezone = result.mappings().first()

        # replace old default timezone on something
        if user.default_timezone == timezone.iana:
            timezones = sorted(await get_timezones(chat_id), key=lambda x: x.id)
            if len(timezones) != 0:
                user.default_timezone = timezones[0].iana
            else:
                user.default_timezone = None

        await session.commit()

        return timezone


async def set_default_timezone(chad_id: int, timezone_id: int):
    async with async_session() as session:
        timezone = await __get_timezone(session, timezone_id)
        user = await __get_user(session, chad_id)

        user.default_timezone = timezone.iana

        await session.commit()
