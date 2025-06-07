from aiogram import Router, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states.states import Registration
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
from services.work_with_json import is_user_registered, save_user_key
from services.get_sales import get_steam_id
from filters.is_creator import IsCreatorFilter
from config.settings_bot import unborn_tier_1_id
from filters.is_not_banned import IsNotBannedFilter

router = Router()

# Как будто бы нет смысла помещать 1 клавиатуру в отдельную папку
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/help"), KeyboardButton(text="/reload_api_key")],
        [KeyboardButton(text="/get_items_resale"), KeyboardButton(text="/get_sale_stats")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

@router.message(Command("start"), IsCreatorFilter())
async def cmd_start_creator(message: types.Message, state: FSMContext):
    if await is_user_registered(unborn_tier_1_id):
        await message.answer(
            "Рад вновь увидеть моего основателя~",
            reply_markup=main_menu_keyboard
        )
        await state.clear()  # на случай, если он был в каком-то состоянии
        logging.info("Наш основатель уже зарегистрировался")
        return
    await message.answer("Добро пожаловать в ваш созданный обитель зла, мой основатель. Пожалуйста, введите ваш API-ключ CSFloat для дальнейшего взаимодействия с ботом")
    await state.set_state(Registration.awaiting_key)
    logging.info(f"Наш основатель пришел, главное не облажаться!")

@router.message(Command("start"), IsNotBannedFilter())
async def start_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if await is_user_registered(user_id):
        await message.answer(
            "👋 Вы уже зарегистрированы. Главное меню:",
            reply_markup=main_menu_keyboard
        )
        await state.clear()  # на случай, если он был в каком-то состоянии
        logging.info("User %s used /start (already registered)", user_id)
        return

    await message.answer("Привет! Я бот-помощник для работы с CSFloat :)\n"
                         "Введите свой api ключ сайта для дальнейшего взаимодействия с ботом")
    await state.set_state(Registration.awaiting_key)
    logging.info(f"User {message.from_user.id} called /start")

@router.message(Registration.awaiting_key)
async def handle_api_key(message: Message, state: FSMContext):
    user_input = message.text.strip()

    steam_id = await get_steam_id(user_input)
    if not steam_id:
        await message.answer("❌ Похоже, вы отправили некорректный ключ. Попробуйте ещё раз.")
        return

    await save_user_key(message.chat.id, user_input, steam_id)
    await message.answer("✅ Ваш API-ключ сохранён! Воспользуйтесь командой /help для понимания функционала бота")
    await message.answer("📋 Главное меню:", reply_markup=main_menu_keyboard)
    await state.clear()

@router.message(Command("help"), IsNotBannedFilter())
async def help_command(message: Message):
    await message.answer(
        "Доступные команды:\n"
        "/get_items_resale - Собрать (обновить) данные по обороту аккаунта\n"
        "/get_sale_stats - Основная статистика по собранной информации\n"
        "/reload_api_key - Поменять свой api ключ"
    )
    logging.info(f"User {message.from_user.id} called /help")