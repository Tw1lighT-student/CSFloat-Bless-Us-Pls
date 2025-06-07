import time
from aiogram import BaseMiddleware
from aiogram.types import Message
import logging

class RateLimitMiddleware(BaseMiddleware):
    """Ограничивает пользователя: не чаще 2 секунд между любыми сообщениями"""
    def __init__(self, limit_seconds: int = 2):
        self.limit_seconds = limit_seconds
        self.user_last_call: dict[int, float] = {}

    async def __call__(self, handler, event: Message, data: dict):
        now = time.time()
        user_id = event.from_user.id

        last_call = self.user_last_call.get(user_id, 0.0)
        if now - last_call < self.limit_seconds:
            logging.info(
                f"Rate-limit: user={user_id} chat={event.chat.id} "
                f"delta={now - last_call:.2f}s ({self.limit_seconds}s limit)"
            )
            await event.answer(f"⚠️ Не так быстро, подожди {self.limit_seconds} сек. и отправь сообщение заново")
            return

        self.user_last_call[user_id] = now
        return await handler(event, data)
