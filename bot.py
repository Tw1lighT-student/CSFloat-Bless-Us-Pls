from config.settings_bot import bot_config
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from routers import registration, main_actions
import asyncio, logging
from middlewares.rate_limit import RateLimitMiddleware

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_fmt = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_fmt)
        logger.addHandler(console_handler)

        file_handler = logging.FileHandler("bot.log", encoding="utf-8", mode="a")
        file_handler.setLevel(logging.INFO)
        file_fmt = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)

async def main():
    bot = Bot(token=bot_config.telegram_api_key)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.message.middleware(RateLimitMiddleware(limit_seconds=2))

    dp.include_router(registration.router)
    dp.include_router(main_actions.router)

    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    setup_logger()
    asyncio.run(main())
