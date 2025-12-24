from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from database.models import UserTimezone, User
from database.request import add_timezone, get_timezone, get_timezones, remove_timezone, get_user, set_default_timezone
from answer.markups.inline_markup import *
from answer.markups.keyboard_markup import *
from answer.states import *
from datetime import datetime
from zoneinfo import ZoneInfo


LAST_MESSAGE_CONTEXT = "last_message"

router = Router()


# Format functions
def format_timezone(zone: UserTimezone) -> str:
    return f"{zone.description} - {ZoneInfo(zone.iana)}"


def format_timezone_user(zone: UserTimezone, user: User) -> str:
    return f"{"⭐️" if zone.iana == user.default_timezone else ""}{zone.description} - {datetime.now(ZoneInfo(zone.iana)).strftime("%H:%M")}"


def format_timezone_numbered(zone: UserTimezone, number: int):
    return f"{number}.  {zone.description} - {ZoneInfo(zone.iana)}"


async def get_timezones_format(chat_id: int) -> str:
    format = []
    for idx, zone in enumerate(await get_timezones(chat_id)):
        format.append(format_timezone_numbered(zone, idx + 1))

    return "\n".join(format)


# State control
async def put_state_message(state: FSMContext, message_id: int, value: str = LAST_MESSAGE_CONTEXT):
    await state.update_data(**{value: message_id})


async def pop_state_message(state: FSMContext, bot: Bot, chat_id: int, value: str = LAST_MESSAGE_CONTEXT):
    if (message_id := await state.get_value(value)) and message_id:
        await bot.delete_message(chat_id, message_id)


async def replace_state_message(state: FSMContext, bot: Bot, chat_id: int, new_message_id: int, pop_value: str = LAST_MESSAGE_CONTEXT, put_value: str = LAST_MESSAGE_CONTEXT):
    await pop_state_message(state, bot, chat_id, pop_value)
    await put_state_message(state, new_message_id, put_value)


# Main
@router.message(CommandStart())
async def start(message: Message):
    await message.answer(text=f"Это бот сделанный с целью сделать работу в разных часовых поясах более удобной.\n\nДля взаимодействия с ботом ответьте на это сообщение.", reply_markup=main_markup)


"""
@router.callback_query(StateFilter(None), F.data == "main")
async def setting_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text="Нa главную 🫡", reply_markup=main_markup)
    await callback.answer()

@router.callback_query(StateFilter(None), F.data == "setting-zones")
async def setting_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text="Настройка часовых поясов:", reply_markup=setting_markup)
    await callback.answer()
"""


@router.message(F.text == CANCEL_REPLY)
async def setting_menu(message: Message, state: FSMContext):
    await state.clear()
    await start(message)


# ADD TIMEZONE
# @router.callback_query(StateFilter(None), F.data == "add-zone")
@router.message(F.text == ADD_TIMEZONE_REPLY)
async def remove_zone(message: Message, state: FSMContext):
    await state.set_state(Add.description)
    message = await message.answer("Введите описание часовой зоны", reply_markup=cancel_markup)
    await put_state_message(state, message.message_id)


@router.message(Add.description)
async def add_timezone_description(message: Message, state: FSMContext, bot: Bot):
    answer: Message
    if len(message.text) < 1:
        answer = await message.answer("Э, ну введи ты описание наконец, дорогой!")
    elif len(message.text) > 30:
        answer = await message.answer("Э, ну браток, давай поменьше описание, длинное слишком! Максимум - 30 символов!")
    else:
        await state.update_data(description=message.text)
        await state.set_state(Add.region)
        answer = await message.answer("Выберите регион часовой зоны:", reply_markup=regions_markup)

    await replace_state_message(state, bot, answer.chat.id, answer.message_id)


@router.callback_query(StateFilter(Add.region), F.data.contains("set-zone-region_"))
async def add_timezone_region(callback: CallbackQuery, state: FSMContext, bot: Bot):
    region = callback.data[callback.data.find("_") + 1:]
    await state.update_data(region=region)
    message = await callback.message.answer("Выберите часовую зону:", reply_markup=get_cities_markup(region))
    await put_state_message(state, message.message_id, value=LAST_MESSAGE_CONTEXT + "_region")

    await state.set_state(Add.city)
    await callback.answer()


@router.callback_query(StateFilter(Add.city), F.data.contains("set-zone-region_"))
async def edit_timezone_region(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await pop_state_message(state, bot, callback.message.chat.id, LAST_MESSAGE_CONTEXT + "_region")

    await add_timezone_region(callback, state, bot)


@router.callback_query(StateFilter(Add.city), F.data.contains("set-zone-city_"))
async def add_timezone_city(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await pop_state_message(state, bot, callback.message.chat.id)
    await pop_state_message(state, bot, callback.message.chat.id, LAST_MESSAGE_CONTEXT + "_region")

    await state.update_data(city=callback.data[callback.data.find("_") + 1:])
    data = await state.get_data()

    await callback.message.answer(f"Добавление часовой зоны\n{data["description"]}: {data["region"]}/{data["city"]}", reply_markup=main_markup)
    await add_timezone(callback.message.chat.id, data)
    # await save_state_message(state, message.message_id, value=LAST_MESSAGE_CONTEXT)

    await state.clear()
    await callback.answer()


"""
@router.message(Add.tzone)
async def add_timezone_offset(message: Message, state: FSMContext):
    text = message.text
    if text[0] == '+':
        text = text[1:]

    if not message.text.isnumeric():
        await message.answer("Ну не, ну ты что творишь? Нужна цифра на сколько твой часовой пояс отличается", reply_markup=setting_cancel_markup)

    else:
        # tzone = timezone(timedelta(hours=int(message.text)))
        tzone = int(message.text)
        await state.update_data(tzone=tzone)
        data = await state.get_data()
        await state.clear()
        await add_timezone(message.chat.id, data)
        await message.answer(f"Добавление нового часового пояса\nОписание: {data.get("description")}\nЧасовая зона: {timezone(timedelta(hours=data.get("tzone")))}", reply_markup=setting_markup)
"""

# Remove zone


@router.message(F.text == REMOVE_TIMEZONE_REPLY)
# @router.callback_query(StateFilter(None), F.data == "remove-zone")
async def remove_zone(message: Message, state: FSMContext):
    user = await get_user(message.chat.id)
    timezones = await get_timezones(message.chat.id)

    if len(timezones) == 0:
        await message.answer(f"Не найдено ни одной зоны!")
    else:
        answer = await message.answer(
            f"Выберите часовую зону для удаления",
            reply_markup=get_timezones_markup(
                timezones,
                lambda zone: format_timezone_user(zone, user)))

        await put_state_message(state, answer.message_id)

        await state.set_state(Remove.id)


@router.callback_query(StateFilter(Remove.id), F.data.contains(CHOSE_TIMEZONE_CALLBACK))
async def choose_delete_id(callback: CallbackQuery, state: FSMContext, bot: Bot):
    delete_id = callback.data[callback.data.find("_") + 1:]
    if not delete_id.isdigit():
        return
    delete_id = int(delete_id)

    zone = await remove_timezone(callback.message.chat.id, delete_id)

    if zone is None:
        return

    await callback.message.answer(f"Удалено {format_timezone(zone)}", reply_markup=main_markup)

    await pop_state_message(state, bot, callback.message.chat.id)
    await state.clear()


# Show time
@router.message(F.text == SHOW_TIME_REPLY)
# @router.callback_query(StateFilter(None), F.data == "time")
async def show_timezones(message: Message):
    user = await get_user(message.chat.id)
    zones = await get_timezones(message.chat.id)
    await message.answer(
        "Часовые зоны:",
        reply_markup=get_timezones_markup(
            zones,
            lambda zone: format_timezone_user(zone, user)
        ))


@router.callback_query(StateFilter(None), F.data.contains(CHOSE_TIMEZONE_CALLBACK))
async def chose_timezone(callback: CallbackQuery, state: FSMContext):
    user = await get_user(callback.message.chat.id)
    timezone_id = callback.data[callback.data.find("_") + 1:]
    if not timezone_id.isdigit():
        return
    timezone_id = int(timezone_id)

    zone = await get_timezone(timezone_id)
    if zone is None:
        return

    await state.set_state(Inspect.action)
    await state.update_data(timezone_id=timezone_id)

    # await callback.message.answer(" ", reply_markup=cancel_markup)
    await callback.message.answer(f"{format_timezone(zone)}", reply_markup=get_inspect_timezone_markup(user.default_timezone == zone.iana))
    await callback.answer()


@router.callback_query(StateFilter(Inspect.action), F.data == INSPECT_DELETE_CALLBACK)
async def delete_inspect_timezone(callback: CallbackQuery, state: FSMContext):
    zone = await remove_timezone(callback.message.chat.id, await state.get_value("timezone_id"))

    await callback.message.answer(f"Удалено {format_timezone(zone)}", reply_markup=main_markup)

    await state.clear()

    user = await get_user(callback.message.chat.id)
    zones = await get_timezones(callback.message.chat.id)

    await callback.message.answer(
        "Часовые зоны:",
        reply_markup=get_timezones_markup(
            zones,
            lambda zone: format_timezone_user(zone, user)
        ))


@router.callback_query(StateFilter(Inspect.action), F.data == INSPECT_MAKE_DEFAULT_CALLBACK)
async def default_inspect_timezone(callback: CallbackQuery, state: FSMContext):
    await set_default_timezone(callback.message.chat.id, await state.get_value("timezone_id"))

    await state.clear()

    user = await get_user(callback.message.chat.id)
    zones = await get_timezones(callback.message.chat.id)

    await callback.message.answer(
        "Часовые зоны:",
        reply_markup=get_timezones_markup(
            zones,
            lambda zone: format_timezone_user(zone, user)
        ))

    await callback.answer()
