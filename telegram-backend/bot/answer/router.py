from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command, CommandObject, StateFilter
from aiogram.types import Message, CallbackQuery
from database.models import UserTimezone, User
from database.request import add_timezone, get_timezone, get_timezones, remove_timezone, get_user, set_default_timezone
from answer.markups.inline_markup import *
from answer.markups.keyboard_markup import *
from answer.states import *
from answer.commands import *
from datetime import datetime, timedelta, timezone
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
async def start(message: Message, bot: Bot):
    await message.answer(text=f"Это бот сделанный с целью сделать работу в разных часовых поясах более удобной.\n\nДля взаимодействия с ботом ответьте на это сообщение.", reply_markup=main_markup)
    await bot.set_my_commands(commands)


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
                lambda zone: format_timezone_user(zone, user),
                cancel_button=True
            ))

        await put_state_message(state, answer.message_id)

        await state.set_state(Remove.id)


@router.callback_query(StateFilter(Remove.id), F.data.contains(CHOSE_TIMEZONE_CALLBACK))
async def choose_delete_id(callback: CallbackQuery, state: FSMContext, bot: Bot):
    delete_id = callback.data[callback.data.find("_") + 1:]

    if delete_id != "cancel":

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
async def answer_timezones(message: Message):
    user = await get_user(message.chat.id)
    zones = await get_timezones(message.chat.id)

    await message.answer(
        "Часовые зоны:",
        reply_markup=get_timezones_markup(
            zones,
            lambda zone: format_timezone_user(zone, user)
        ))


@router.message(StateFilter(None), F.text == SHOW_TIME_REPLY)
@router.message(StateFilter(Inspect.action), F.text == SHOW_TIME_REPLY)
async def show_timezones(message: Message):
    await answer_timezones(message)


@router.callback_query(StateFilter(None), F.data.contains(CHOSE_TIMEZONE_CALLBACK))
@router.callback_query(StateFilter(Inspect.action), F.data.contains(CHOSE_TIMEZONE_CALLBACK))
async def chose_timezone(callback: CallbackQuery, state: FSMContext, bot: Bot):
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
    answer = await callback.message.answer(f"{format_timezone(zone)}", reply_markup=get_inspect_timezone_markup(user.default_timezone == zone.iana))
    await replace_state_message(state, bot, answer.chat.id, answer.message_id)

    await callback.answer()


@router.callback_query(StateFilter(Inspect.action), F.data == INSPECT_DELETE_CALLBACK)
async def delete_inspect_timezone(callback: CallbackQuery, state: FSMContext, bot: Bot):
    zone = await remove_timezone(callback.message.chat.id, await state.get_value("timezone_id"))

    await callback.message.answer(f"Удалено {format_timezone(zone)}", reply_markup=main_markup)

    await pop_state_message(state, bot, callback.message.chat.id)
    await state.clear()

    await answer_timezones(callback.message)


@router.callback_query(StateFilter(Inspect.action), F.data == INSPECT_MAKE_DEFAULT_CALLBACK)
async def default_inspect_timezone(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await set_default_timezone(callback.message.chat.id, await state.get_value("timezone_id"))

    await pop_state_message(state, bot, callback.message.chat.id)
    await state.clear()

    await answer_timezones(callback.message)

    await callback.answer()


@router.callback_query(StateFilter(Inspect.action), F.data == INSPECT_CANCEL_CALLBACK)
async def cancel_inspect(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await pop_state_message(state, bot, callback.message.chat.id)

    await state.clear()
    await callback.answer()

    # await callback.message.answer("Возврат к главному меню", reply_markup=main_markup)
    # await answer_timezones(callback.message)


# Commands
def parse_time(str: str, tz: ZoneInfo) -> tuple[datetime, bool] | tuple[None, None]:
    date = str.split(".")
    time = date[-1].split(":")

    if len(time) < 2 or not (time[-1].isdigit() and time[-2].isdigit()):
        return None

    hours, minutes = map(int, (time[-2], time[-1]))
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        return None

    for i in date[:-1]:
        if not i.isdigit():
            return None

    date = list(map(int, date[-2::-1]))

    # now = datetime.now()
    day, month, year, *_ = *date, None, None, None

    has_only_time = False

    if year is None:
        now = datetime.now(tz)
        year = now.year

        if month is None:
            month = now.month

            if day is None:
                day = now.day
                has_only_time = True

    elif year < 2000:
        year += 2000

    try:
        dt = datetime(year, month, day, hour=hours, minute=minutes, tzinfo=tz)
    except:
        return None, None

    return dt, has_only_time


@router.message(Command(SUGGEST_TIME_COMMAND))
async def suggest_time_command(message: Message, command: CommandObject, bot: Bot):
    if command.args is None:
        await message.reply("Введите время в формате ЧЧ:ММ!\nОпционально можно добавить год, дату и месяц, пример:\nГГ.ММ.ДД.ЧЧ:ММ, ММ.ДД.ЧЧ:ММ или ДД.ЧЧ:ММ")
        return

    time_split_start = command.args.find(" ") + 1
    time_split_end = command.args.find(" ", time_split_start)
    if time_split_end == -1:
        time_split_end = len(command.args) - time_split_start

    time_str = command.args[time_split_start: time_split_end]

    user = await get_user(message.from_user.id)
    if user is None:
        return

    dt, has_only_time = parse_time(time_str, ZoneInfo(user.default_timezone))
    if dt == None:
        await message.reply("Введите время в формате ЧЧ:ММ!\nОпционально можно добавить год, дату и месяц, пример:\nГГГГ.ММ.ДД.ЧЧ:ММ, ММ.ДД.ЧЧ:ММ или ДД.ЧЧ:ММ")
        return

    await message.reply(f"Время в своей часовой зоне: {dt.strftime(f"%H:%M" if has_only_time else f"%Y.%m.%d.%H:%M")}",
                        reply_markup=get_gettime_markup(dt.strftime(f"%H:%M_{user.default_timezone}" if has_only_time else f"%Y.%m.%d.%H:%M_{user.default_timezone}")))


@router.callback_query(F.data.contains(SHOW_GETTIME))
async def show_get_time_callback(callback: CallbackQuery):
    if callback.data == None:
        return

    data_start = callback.data.find("_") + 1
    user_start = callback.data.find("_", data_start) + 1

    dt, has_only_time = parse_time(
        callback.data[data_start:user_start - 1], ZoneInfo(callback.data[user_start:]))

    if dt == None:
        return

    user = await get_user(callback.from_user.id)
    if user is None:
        dt = dt.astimezone(timezone.utc)
    else:
        dt = dt.astimezone(ZoneInfo(user.default_timezone))

    await callback.message.reply(
        f"Время: {dt.strftime("%H:%M") if has_only_time else dt.isoformat(" ")}{" в UTC=0 зоне\nДля того чтобы узнать время в вашем часовом поясе настройте их в личных сообщениях у бота" if user is None else ""}")

    await callback.answer()
