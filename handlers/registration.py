from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from states.registration import RegistrationStates
from keyboards.reply import get_main_menu, get_gender_keyboard, get_looking_for_keyboard, get_purpose_keyboard, get_location_keyboard
import database.db as db
import aiohttp

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if user:
        await message.answer(
            f"С возвращением, {user['name']}! 👋",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            "Добро пожаловать в бот для знакомств! Давайте создадим вашу анкету.\nКак вас зовут?",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(RegistrationStates.waiting_for_name)

@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько вам лет?")
    await state.set_state(RegistrationStates.waiting_for_age)

@router.message(RegistrationStates.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit() or not (14 <= int(message.text) <= 100):
        await message.answer("Пожалуйста, введите корректный возраст (число от 14 до 100).")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Ваш пол?", reply_markup=get_gender_keyboard())
    await state.set_state(RegistrationStates.waiting_for_gender)

@router.message(RegistrationStates.waiting_for_gender)
async def process_gender(message: Message, state: FSMContext):
    if message.text not in ["Парень", "Девушка"]:
        await message.answer("Пожалуйста, выберите пол, используя кнопки ниже.", reply_markup=get_gender_keyboard())
        return
    await state.update_data(gender=message.text)
    await message.answer("Кого вы ищете?", reply_markup=get_looking_for_keyboard())
    await state.set_state(RegistrationStates.waiting_for_looking_for)

@router.message(RegistrationStates.waiting_for_looking_for)
async def process_looking_for(message: Message, state: FSMContext):
    if message.text not in ["Парня", "Девушку", "Всех"]:
        await message.answer("Пожалуйста, выберите, кого вы ищете, используя кнопки.", reply_markup=get_looking_for_keyboard())
        return
    await state.update_data(looking_for=message.text)
    await message.answer("Для чего вы решили воспользоваться ботом Burning Love?", reply_markup=get_purpose_keyboard())
    await state.set_state(RegistrationStates.waiting_for_purpose)

@router.message(RegistrationStates.waiting_for_purpose)
async def process_purpose(message: Message, state: FSMContext):
    valid_purposes = [
        "Поиск секса/одноразового развлечения",
        "Поиск отношения",
        "Создание семьи",
        "Дружба",
        "Поиск тимейта для игры",
        "Поиск творческого партнёра(Музыкальная группа)"
    ]
    if message.text not in valid_purposes:
        await message.answer("Пожалуйста, выберите цель из предложенных вариантов.", reply_markup=get_purpose_keyboard())
        return
    await state.update_data(purpose=message.text)
    await message.answer("В каком городе вы находитесь? Вы можете отправить геолокацию или просто написать название города.", reply_markup=get_location_keyboard())
    await state.set_state(RegistrationStates.waiting_for_city)

async def get_city_from_coords(lat: float, lon: float) -> str:
    headers = {"User-Agent": "TelogramBot/1.0"}
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10&addressdetails=1&accept-language=ru"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    address = data.get("address", {})
                    return address.get("city") or address.get("town") or address.get("village") or address.get("state") or "Неизвестный город"
    except Exception:
        pass
    return "Неизвестный город"

@router.message(RegistrationStates.waiting_for_city, F.location)
async def process_city_location(message: Message, state: FSMContext):
    msg = await message.answer("Определяю город по координатам... ⏳", reply_markup=ReplyKeyboardRemove())
    lat = message.location.latitude
    lon = message.location.longitude
    
    city = await get_city_from_coords(lat, lon)
    
    await state.update_data(city=city)
    await msg.delete()
    await message.answer(f"Определен город: {city}\n\nНапишите немного о себе:")
    await state.set_state(RegistrationStates.waiting_for_description)

@router.message(RegistrationStates.waiting_for_city, F.text)
async def process_city_text(message: Message, state: FSMContext):
    await state.update_data(city=message.text.strip().title())
    await message.answer("Напишите немного о себе:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegistrationStates.waiting_for_description)

@router.message(RegistrationStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Теперь отправьте ваше фото (просто картинку):")
    await state.set_state(RegistrationStates.waiting_for_photo)

@router.message(RegistrationStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    user_data = await state.get_data()
    
    await db.add_user(
        user_id=message.from_user.id,
        name=user_data['name'],
        age=user_data['age'],
        gender=user_data['gender'],
        looking_for=user_data['looking_for'],
        purpose=user_data['purpose'],
        city=user_data['city'],
        description=user_data['description'],
        photo=photo_id,
        username=message.from_user.username
    )
    
    await state.clear()
    await message.answer(
        "Ваша анкета успешно создана! 🎉",
        reply_markup=get_main_menu()
    )

@router.message(RegistrationStates.waiting_for_photo)
async def process_photo_invalid(message: Message):
    await message.answer("Пожалуйста, отправьте фотографию.")

@router.message(F.text == "👤 Моя анкета")
async def show_my_profile(message: Message):
    user = await db.get_user(message.from_user.id)
    if user:
        caption = f"{user['name']}, {user['age']}, {user['city']}\nЦель: {user['purpose']}\n\n{user['description']}"
        from keyboards.inline import get_profile_keyboard
        await message.answer_photo(photo=user['photo'], caption=caption, reply_markup=get_profile_keyboard())
    else:
        await message.answer("Анкета не найдена. Нажмите /start для регистрации.")

from aiogram.types import CallbackQuery

@router.callback_query(F.data == "edit_profile")
async def process_edit_profile(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Давайте обновим вашу анкету.\nКак вас зовут?",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(RegistrationStates.waiting_for_name)
    await callback.answer()

@router.callback_query(F.data == "delete_profile")
async def process_delete_profile(callback: CallbackQuery):
    await db.delete_user(callback.from_user.id)
    await callback.message.answer(
        "Ваша анкета успешно удалена. 🗑️\nНажмите /start, чтобы создать новую.",
        reply_markup=ReplyKeyboardRemove()
    )
    await callback.message.delete()
    await callback.answer()

@router.message(F.text == "🆘 Поддержка")
async def show_support(message: Message):
    from keyboards.inline import get_support_keyboard
    await message.answer(
        "Возникли вопросы или предложения? Вы можете написать нам в Discord или в аккаунт поддержки Telegram! 🆘",
        reply_markup=get_support_keyboard()
    )
