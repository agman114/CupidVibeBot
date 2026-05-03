from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_gender = State()
    waiting_for_looking_for = State()
    waiting_for_purpose = State()
    waiting_for_city = State()
    waiting_for_description = State()
    waiting_for_media = State()

class EditProfileStates(StatesGroup):
    edit_name = State()
    edit_age = State()
    edit_city = State()
    edit_description = State()
    edit_media = State()
    edit_gender = State()
    edit_looking_for = State()
    edit_purpose = State()

class SuperLikeStates(StatesGroup):
    waiting_for_message = State()
