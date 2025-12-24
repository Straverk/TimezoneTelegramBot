from aiogram.fsm.state import State, StatesGroup


class Add(StatesGroup):
    description = State()
    region = State()
    city = State()


class Remove(StatesGroup):
    id = State()


class Inspect(StatesGroup):
    action = State()
