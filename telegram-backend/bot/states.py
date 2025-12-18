from aiogram.fsm.state import State, StatesGroup


class Add(StatesGroup):
    description = State()
    tzone = State()


class Remove(StatesGroup):
    id = State()
