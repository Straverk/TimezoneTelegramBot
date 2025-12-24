from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


SHOW_TIME_REPLY = "🕐 Показать время"
ADD_TIMEZONE_REPLY = "➕ Добавить зону"
REMOVE_TIMEZONE_REPLY = "🗑 Удалить зону"

CANCEL_REPLY = "❌ Отменить"

main_markup = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=SHOW_TIME_REPLY),
            KeyboardButton(text=ADD_TIMEZONE_REPLY),
            KeyboardButton(text=REMOVE_TIMEZONE_REPLY),
        ]
    ],
    resize_keyboard=True
)

cancel_markup = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=CANCEL_REPLY)
        ]
    ],
    resize_keyboard=True
)
