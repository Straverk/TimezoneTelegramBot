import sys
from os import getenv
import asyncio
from aiogram import Bot, Dispatcher
from answer.router import router
from database.models import async_main


BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"


async def main():
    await async_main()

    token = getenv(BOT_TOKEN_ENV)
    if token == None:
        print(f"Not found {BOT_TOKEN_ENV} enviroment variable")
        raise Exception("Not found " + BOT_TOKEN_ENV + " enviroment variable")

    bot = Bot(token)
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot was stopped by KeyboardInterrupt!")
    except Exception:
        print("\nSomething went with exception:\n")
        raise sys.exception()
