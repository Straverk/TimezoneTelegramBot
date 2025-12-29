from aiogram.types import BotCommand


SUGGEST_TIME_COMMAND = "time"

commands = [
    BotCommand(command=SUGGEST_TIME_COMMAND,
               description="Предложить время в формате: **ГГ.ММ.ДД.ЧЧ:ММ**, **ДД.ЧЧ:ММ ** или **ММ.ДД.ЧЧ:ММ**",
               language_code="ru"),

    BotCommand(command=SUGGEST_TIME_COMMAND,
               description="Suggest the time in the format: **YY.MM.DD.HH:MM**, **DD.HH:MM ** или **MM.DD.HH:MM**")
]
