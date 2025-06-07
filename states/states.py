from aiogram.fsm.state import StatesGroup, State

class Registration(StatesGroup):
    awaiting_key = State()

class Parser(StatesGroup):
    awaiting_weeks = State()