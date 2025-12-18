from typing import Any, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import async_session
from database.models import User, Timezone


def get_user_select(chat_id):
    return select(User).where(User.chat_id == chat_id)


async def __get_user(session: AsyncSession, chat_id: int) -> User | None:
    return (await session.scalars(get_user_select(chat_id))).first()


async def __get_or_add_user(session: AsyncSession, chat_id: int) -> User:
    user = await __get_user(session, chat_id)

    if user is None:
        user = User(chat_id=chat_id)
        session.add(user)
        await session.flush()

    return user


async def add_timezone(chat_id: int, data):
    async with async_session() as session:
        user = await __get_or_add_user(session, chat_id)

        # Logical solution
        session.add(Timezone(
            description=data["description"],
            tzone=data["tzone"],
            user_id=user.id
        ))

        # Using SQL Alchemy "magic", this doesn't work correct with new users
        """
        user.timezones.append(Timezone(
            description=data["description"],
            tzone=data["tzone"],
            user_id=user.id
        ))
        """

        await session.commit()


async def get_timezones(chat_id: int) -> Tuple[Timezone]:
    async with async_session() as session:
        user = await __get_user(session, chat_id)

        if user is None:
            return tuple()

        return tuple(user.timezones)


async def remove_timezone(chat_id: int, delete_id: int) -> Tuple[Timezone] | None:
    async with async_session() as session:
        user = await __get_user(session, chat_id)

        if user is None:
            return None

        if len(user.timezones) < delete_id:
            return None
        else:
            return user.timezones.pop(delete_id)
