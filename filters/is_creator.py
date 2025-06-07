from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from config.settings_bot import unborn_tier_1_id, ankor_id

class IsCreatorFilter(BaseFilter):
    """Для создателей такого тг бота нужно отдельное поведение, что и позволяет этот класс сделать"""
    async def __call__(self, event, *_, **__) -> bool:
        if isinstance(event, (Message, CallbackQuery)):
            return event.from_user.id == unborn_tier_1_id or event.from_user.id == ankor_id
        return False