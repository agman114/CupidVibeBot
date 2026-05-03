from aiogram.fsm.state import State, StatesGroup

class FilterStates(StatesGroup):
    waiting_for_age_range = State()
