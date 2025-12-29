from typing import Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from zoneinfo import available_timezones
from database.models import UserTimezone


timezones = {}

for zone in available_timezones():
    format = zone.split("/")
    if len(format) == 2:
        if format[0] not in timezones:
            timezones[format[0]] = [format[1]]
        else:
            timezones[format[0]].append(format[1])

regions = sorted(list(timezones.keys()),
                 key=lambda a: "z" if a == "Etc" else a[0])

"""
main_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Настроить пояса", callback_data="setting-zones"),
         InlineKeyboardButton(text="🕐 Показать время", callback_data="time")]
    ]
)"""


def __get_region(idx: int):
    return InlineKeyboardButton(
        text=regions[idx],
        callback_data="set-zone-region_" + regions[idx])


regions_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        ([__get_region(i), __get_region(i + 1)] if i + 1 < len(timezones) else
         [__get_region(i)]
         ) for i in range(0, len(timezones), 2)
    ])


def __get_city(cities, idx: int):
    return InlineKeyboardButton(
        text=cities[idx],
        callback_data="set-zone-city_" + cities[idx])


def get_cities_markup(region: str):
    cities = sorted(timezones[region])
    region_len = len(cities)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            ([__get_city(cities, i), __get_city(cities, i+1), __get_city(cities, i+2)] if i + 2 < region_len else
             ([__get_city(cities, i), __get_city(cities, i+1)] if i + 1 < region_len else
             [__get_city(cities, i)])
             ) for i in range(0, region_len, 3)
        ]
    )


CHOSE_TIMEZONE_CALLBACK = "chose-timezone_"


def __default_timezone_format(timezone: UserTimezone) -> str:
    return f"{timezone.description}: {timezone.iana}"


def get_timezones_markup(timezones: Tuple[UserTimezone], text_format=__default_timezone_format, cancel_button: bool = False):
    keyboard = [[InlineKeyboardButton(text=text_format(
        timezone), callback_data=CHOSE_TIMEZONE_CALLBACK + str(timezone.id))] for timezone in timezones]

    if cancel_button:
        keyboard.append([InlineKeyboardButton(
            text="❌ Назад", callback_data=CHOSE_TIMEZONE_CALLBACK + "cancel")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


INSPECT_MAKE_DEFAULT_CALLBACK = "make-default"
INSPECT_DELETE_CALLBACK = "delete"
INSPECT_CANCEL_CALLBACK = "cancel"


def get_inspect_timezone_markup(is_default: bool):
    buttons = [
        [
            InlineKeyboardButton(
                text="🗑 Удалить ", callback_data=INSPECT_DELETE_CALLBACK),
            InlineKeyboardButton(
                text="❌ Назад", callback_data=INSPECT_CANCEL_CALLBACK)
        ]
    ]
    if not is_default:
        buttons[0].insert(0, InlineKeyboardButton(
            text="️️️️️⭐️ Сделать основной", callback_data=INSPECT_MAKE_DEFAULT_CALLBACK))

    return InlineKeyboardMarkup(inline_keyboard=buttons)


SHOW_GETTIME = "get-time_"


def get_gettime_markup(id: str):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(
            text="Время", callback_data=SHOW_GETTIME + id)]]
    )

    return markup
