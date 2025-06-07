from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from services.work_with_json import is_user_banned

class IsNotBannedFilter(BaseFilter):
    """Вручную записываем в json файл storage/ban_list user_id, и класс проверяет и в случае чего банит крипчиков"""
    async def __call__(self, event, *_, **__) -> bool:
        user_id = getattr(event.from_user, "id", None)
        if not user_id:
            return False

        if await is_user_banned(user_id):
            text = "🚫 Вы в черном списке и не можете использовать бота."
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
            return False

        return True