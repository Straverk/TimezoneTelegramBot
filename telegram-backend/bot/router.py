from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message, CallbackQuery
from database.models import Timezone
from database.request import add_timezone, get_timezones, remove_timezone
from keyboard_markup import main_markup, setting_cancel_markup, setting_markup
from states import *
from datetime import timezone, timedelta, datetime


router = Router()


def format_timezone(zone: Timezone) -> str:
    return " - ".join(zone.description, timezone(timedelta(hours=zone.tzone)))


def format_timezone_numbered(zone: Timezone, number: int):
    return f"{number}.  {zone.description} - {timezone(timedelta(hours=zone.tzone))}"


async def get_timezones_format(chat_id: int) -> str:
    format = []
    for idx, zone in enumerate(await get_timezones(chat_id)):
        format.append(format_timezone_numbered(zone, idx + 1))

    return "\n".join(format)


# Main in-out
@router.message(CommandStart())
async def start(message: Message):
    print(message.from_user.full_name)
    await message.answer(text=f"Э, {message.from_user.full_name}, здарова, чё делать будем?", reply_markup=main_markup)


@router.callback_query(StateFilter(None), F.data == "main")
async def setting_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text="Нa главную 🫡", reply_markup=main_markup)
    await callback.answer()


@router.callback_query(StateFilter(None), F.data == "setting-zones")
async def setting_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text="Настройка часовых поясов:", reply_markup=setting_markup)
    await callback.answer()


@router.callback_query(F.data == "cancel-setting")
async def setting_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(text="Отмена", reply_markup=setting_markup)
    await callback.answer()


# Add zone
@router.callback_query(StateFilter(None), F.data == "add-zone")
async def remove_zone(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Add.description)
    await callback.message.answer("Введите описание часовой зоны", reply_markup=setting_cancel_markup)
    await callback.answer()


@router.message(Add.description)
async def add_timezone_description(message: Message, state: FSMContext):
    if len(message.text) < 1:
        await message.answer("Э, ну введи ты описание наконец, дорогой!", reply_markup=setting_cancel_markup)
    elif len(message.text) > 30:
        await message.answer("Э, ну браток, давай поменьше описание, длинное слишком! Максимум - 30 символов!")
    else:
        await state.update_data(description=message.text)
        await state.set_state(Add.tzone)
        await message.answer(f"Описание установленно, теперь введите свой часовой пояс относительно этого времени: {datetime.now(timezone.utc).strftime("%H:%M")}")


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


# Remove zone
@router.callback_query(StateFilter(None), F.data == "remove-zone")
async def remove_zone(callback: CallbackQuery, state: FSMContext):
    format_timezones = await get_timezones_format(callback.message.chat.id)
    callback.answer()
    if format_timezones == "":
        await callback.message.answer(f"Не найдено ни одной зоны!")
    else:
        await callback.message.answer(f"Введите номер часовой зоны для удаления\n{format_timezones}", reply_markup=setting_cancel_markup)
        await state.set_state(Remove.id)
    await callback.answer()


@router.message(Remove.id)
async def choose_delete_id(message: Message, state: FSMContext):
    if not message.text.isnumeric() or int(message.text) < 1:
        await message.answer("Э, ну даже без бд вижу ты какую-то дичь творишь, не похоже это на число!", reply_markup=setting_cancel_markup)
    else:
        id = (await state.get_data()).get("id") + 1
        if id < 1:
            await message.answer("Да-да, очень смешно, а теперь вводи нормальное число")

        zone = await remove_timezone(message.chat.id, id)

        if zone is None:
            await message.answer("Введено некорректное число")

        await message.answer(f"Удалено {format_timezone(zone)}", reply_markup=setting_markup)
        await state.clear()


# Show time
@router.callback_query(StateFilter(None), F.data == "time")
async def time(callback: CallbackQuery):
    format = ["Местное время:"]
    for zone in await get_timezones(callback.message.chat.id):
        format.append(
            f"{zone.description} - {datetime.now(timezone(timedelta(hours=zone.tzone))).strftime("%H:%M")}")
    await callback.message.answer("\n".join(format))
    await callback.answer()
