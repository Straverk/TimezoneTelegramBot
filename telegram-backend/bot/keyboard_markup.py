from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton


main_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Настроить пояса", callback_data="setting-zones"),
         InlineKeyboardButton(text="🕐 Показать время", callback_data="time")]
    ]
)


setting_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Удалить зону", callback_data="remove-zone"),
         InlineKeyboardButton(text="➕ Добавить зону",
                              callback_data="add-zone"),
         InlineKeyboardButton(text="🔙 Назад", callback_data="main")]
    ]
)

setting_cancel_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(
            text="❌ Отменить", callback_data="cancel-setting")]
    ]
)
