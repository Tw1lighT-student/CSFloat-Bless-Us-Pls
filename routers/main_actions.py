from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states.states import Parser, Registration
from services.work_with_json import get_user_key_by_id
import logging
from services.get_sales import fetch_all_sales, user_cache
from services.work_with_database import get_stats
from filters.is_not_banned import IsNotBannedFilter

router = Router()

def last_table_for(user_id: int):
    """Берем последнюю таблицу, на которую был запрос"""
    tables = user_cache.get(user_id)
    if not tables:
        return None
    return max(tables.items(), key=lambda kv: kv[1]["accessed"])[0]

@router.message(Command("reload_api_key"), IsNotBannedFilter())
async def reload_command(message: Message, state: FSMContext):
    await message.answer("Введите новый api ключ для CSFloat")
    await state.set_state(Registration.awaiting_key)
    logging.info(f"User {message.from_user.id} called /reload_api_key")

@router.message(Command("get_items_resale"), IsNotBannedFilter())
async def get_items_command(message: Message, state: FSMContext):
    await message.answer("Введите кол-во недель, за которое вы хотите получить статистику. Если вы хотите получить статистику за все время введите 'All time'")
    await state.set_state(Parser.awaiting_weeks)
    logging.info(f"User {message.from_user.id} called /get_items_resale")

@router.message(Parser.awaiting_weeks)
async def weeks_input(message: Message, state: FSMContext):
    weeks = message.text.strip()
    if weeks == 'All time' or str(weeks).isdigit():
        api_key, steam_id = await get_user_key_by_id(message.chat.id)

        if not api_key:
            await message.answer(
                "Вы ещё не зарегистрированы.\n"
                "Отправьте команду /start и укажите свой API-ключ."
            )
            await state.clear()
            return

        if str(weeks).isdigit():
            await fetch_all_sales(steam_id, api_key, message.from_user.id, int(weeks))
        else:
            await fetch_all_sales(steam_id, api_key, message.from_user.id)
        await message.answer('Парсинг данных окончен')
        await state.clear()
    else:
        await message.answer('Вы ввели символы, не соответствующие нашим условиям. Попробуйте еще раз')
        return

@router.message(Command("get_sale_stats"), IsNotBannedFilter())
async def send_stats_command(message: Message):
    table = last_table_for(message.from_user.id)
    if table is None:
        await message.answer("Сначала загрузите продажи (/get_items_resale).")
        return

    stats = await get_stats(table)

    text = (
        "📊 *Оборот аккаунта*\n"
        f"Всего сделок: {stats['total']['count']}\n"
        f"Оборот: {stats['total']['sum']} $\n\n"

        "💸 *Продажи*\n"
        f"  • {stats['sales']['count']} шт. / {stats['sales']['sum']} $\n"
        f"  • Дороже всего: {stats['sales']['max']['item']} – {stats['sales']['max']['price']} $\n"
        f"  • Дешевле всего: {stats['sales']['min']['item']} – {stats['sales']['min']['price']} $\n"
        f"  • Медиана цены: {stats['sales']['median']} $\n\n"

        "🛒 *Покупки*\n"
        f"  • {stats['purchases']['count']} шт. / {stats['purchases']['sum']} $\n"
        f"  • Дороже всего: {stats['purchases']['max']['item']} – {stats['purchases']['max']['price']} $\n"
        f"  • Дешевле всего: {stats['purchases']['min']['item']} – {stats['purchases']['min']['price']} $\n"
        f"  • Медиана цены: {stats['purchases']['median']} $\n"
    )
    await message.answer(text, parse_mode="Markdown")
    logging.info(f"User {message.from_user.id} called /get_sale_stats")




