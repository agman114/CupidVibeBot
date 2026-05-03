from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states.filters import FilterStates
from keyboards.inline import get_filters_keyboard
import database.db as db

router = Router()

@router.message(F.text == "⚙️ Настройки поиска")
async def show_filters(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала необходимо зарегистрироваться. Нажмите /start")
        return
    await message.answer("Настройки поиска:", reply_markup=get_filters_keyboard(user))

@router.callback_query(F.data.startswith("filter_"))
async def process_filter_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    
    action = callback.data
    
    if action == "filter_age":
        await callback.message.answer("Введите диапазон возраста (например, 18-25) или конкретный возраст (например, 20):")
        await state.set_state(FilterStates.waiting_for_age_range)
        await callback.answer()
        return
        
    elif action == "filter_city":
        new_val = 0 if user["filter_city_only"] else 1
        await db.update_user_filter(user_id, "filter_city_only", new_val)
        
    elif action == "filter_purposes_menu":
        from keyboards.inline import get_purposes_filter_keyboard
        await callback.message.edit_reply_markup(reply_markup=get_purposes_filter_keyboard(user))
        await callback.answer()
        return
        
    # Обновляем клавиатуру после изменения
    user = await db.get_user(user_id)
    await callback.message.edit_reply_markup(reply_markup=get_filters_keyboard(user))
    await callback.answer()

@router.message(FilterStates.waiting_for_age_range)
async def process_age_range(message: Message, state: FSMContext):
    try:
        parts = message.text.split("-")
        if len(parts) == 1:
            min_age = max_age = int(parts[0].strip())
        elif len(parts) == 2:
            min_age = int(parts[0].strip())
            max_age = int(parts[1].strip())
        else:
            raise ValueError
        
        if not (14 <= min_age <= max_age <= 100):
            raise ValueError
            
        await db.update_user_filter(message.from_user.id, "filter_age_min", min_age)
        await db.update_user_filter(message.from_user.id, "filter_age_max", max_age)
        
        user = await db.get_user(message.from_user.id)
        await message.answer("Возрастной фильтр обновлен! Текущие настройки:", reply_markup=get_filters_keyboard(user))
        await state.clear()
        
    except ValueError:
        await message.answer("Пожалуйста, введите корректный возраст (например, 20) или диапазон (например, 18-25). Возраст должен быть от 14 до 100 лет.")

@router.callback_query(F.data == "filter_back")
async def process_filter_back(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=get_filters_keyboard(user))
    await callback.answer()

from keyboards.inline import VALID_PURPOSES

@router.callback_query(F.data.startswith("purpose_toggle_"))
async def process_purpose_toggle(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    
    action = callback.data.replace("purpose_toggle_", "")
    current_purposes_str = dict(user).get("filter_purposes") or ""
    selected_purposes = current_purposes_str.split(",") if current_purposes_str else []
    
    if action == "all":
        selected_purposes = []
    else:
        idx = int(action)
        p = VALID_PURPOSES[idx]
        if p in selected_purposes:
            selected_purposes.remove(p)
        else:
            selected_purposes.append(p)
            
    new_purposes_str = ",".join(selected_purposes)
    await db.update_user_filter(user_id, "filter_purposes", new_purposes_str)
    
    user = await db.get_user(user_id)
    from keyboards.inline import get_purposes_filter_keyboard
    await callback.message.edit_reply_markup(reply_markup=get_purposes_filter_keyboard(user))
    await callback.answer()
