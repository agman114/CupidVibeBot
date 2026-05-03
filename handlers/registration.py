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
    if user and user['name']:
        await message.answer(
            f"С возвращением, {user['name']}! 👋",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            "<b>Бот создан ClimaxGroup</b>\n\nДобро пожаловать в бот для знакомств! Давайте создадим вашу анкету.\nКак вас зовут?",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML"
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

from keyboards.reply import get_main_menu, get_gender_keyboard, get_looking_for_keyboard, get_purpose_keyboard, get_location_keyboard, get_media_keyboard

@router.message(RegistrationStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(
        "Теперь отправьте до 5 фото или видео для вашей анкеты.\n"
        "Вы можете отправлять их по одному. Когда закончите, нажмите кнопку «Завершить».",
        reply_markup=get_media_keyboard()
    )
    await state.update_data(media=[])
    await state.set_state(RegistrationStates.waiting_for_media)

@router.message(RegistrationStates.waiting_for_media, F.photo | F.video)
async def process_media(message: Message, state: FSMContext):
    data = await state.get_data()
    media_list = data.get("media", [])
    
    if len(media_list) >= 5:
        await message.answer("Вы уже загрузили 5 медиафайлов. Нажмите «Завершить», чтобы продолжить.")
        return

    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    else:
        file_id = message.video.file_id
        file_type = "video"
        
    media_list.append({"file_id": file_id, "file_type": file_type})
    await state.update_data(media=media_list)
    
    await message.answer(f"Загружено {len(media_list)}/5. Отправьте еще или нажмите «Завершить».")

@router.message(RegistrationStates.waiting_for_media, F.text == "✅ Завершить")
async def process_media_done(message: Message, state: FSMContext):
    user_data = await state.get_data()
    media_list = user_data.get("media", [])
    
    if not media_list:
        await message.answer("Пожалуйста, загрузите хотя бы одно фото или видео.")
        return
        
    main_photo = None
    for m in media_list:
        if m["file_type"] == "photo":
            main_photo = m["file_id"]
            break
            
    await db.add_user(
        user_id=message.from_user.id,
        name=user_data['name'],
        age=user_data['age'],
        gender=user_data['gender'],
        looking_for=user_data['looking_for'],
        purpose=user_data['purpose'],
        city=user_data['city'],
        description=user_data['description'],
        photo=main_photo or media_list[0]["file_id"],
        username=message.from_user.username
    )
    
    await db.clear_user_media(message.from_user.id)
    for m in media_list:
        await db.add_user_media(message.from_user.id, m["file_id"], m["file_type"])
    
    await state.clear()
    await message.answer(
        "Ваша анкета успешно создана! 🎉",
        reply_markup=get_main_menu()
    )

@router.message(RegistrationStates.waiting_for_media)
async def process_media_invalid(message: Message):
    await message.answer("Пожалуйста, отправьте фотографию, видео или нажмите «Завершить».")

@router.message(F.text == "👤 Моя анкета")
async def show_my_profile(message: Message):
    user = await db.get_user(message.from_user.id)
    if user:
        media = await db.get_user_media(message.from_user.id)
        
        name_str = f"<b>{user['name']}</b>"
        if user['is_vip']: name_str += " 💎"
        if user['is_verified']: name_str += " ✅"
        
        caption = f"{name_str}, {user['age']}, {user['city']}\nЦель: {user['purpose']}\n\n{user['description']}"
        from keyboards.inline import get_profile_keyboard
        
        if not media:
            await message.answer_photo(photo=user['photo'], caption=caption, reply_markup=get_profile_keyboard(), parse_mode="HTML")
        elif len(media) == 1:
            m = media[0]
            if m['file_type'] == 'photo':
                await message.answer_photo(photo=m['file_id'], caption=caption, reply_markup=get_profile_keyboard(), parse_mode="HTML")
            else:
                await message.answer_video(video=m['file_id'], caption=caption, reply_markup=get_profile_keyboard(), parse_mode="HTML")
        else:
            from aiogram.types import InputMediaPhoto, InputMediaVideo
            media_group = []
            for i, m in enumerate(media):
                if m['file_type'] == 'photo':
                    media_group.append(InputMediaPhoto(media=m['file_id'], caption=caption if i == 0 else None, parse_mode="HTML"))
                else:
                    media_group.append(InputMediaVideo(media=m['file_id'], caption=caption if i == 0 else None, parse_mode="HTML"))
            
            await message.answer_media_group(media=media_group)
            await message.answer("Управление анкетой:", reply_markup=get_profile_keyboard())
    else:
        await message.answer("Анкета не найдена. Нажмите /start для регистрации.")

from aiogram.types import CallbackQuery

from states.registration import RegistrationStates, EditProfileStates

@router.callback_query(F.data == "edit_menu")
async def show_edit_menu(callback: CallbackQuery):
    from keyboards.inline import get_edit_profile_keyboard
    await callback.message.edit_reply_markup(reply_markup=get_edit_profile_keyboard())
    await callback.answer()

@router.callback_query(F.data == "show_profile")
async def show_profile_callback(callback: CallbackQuery):
    await callback.message.delete()
    await show_my_profile(callback.message)
    await callback.answer()

# Handlers for starting individual field edits
@router.callback_query(F.data.startswith("edit_field_"))
async def start_field_edit(callback: CallbackQuery, state: FSMContext):
    field = callback.data.replace("edit_field_", "")
    
    if field == "name":
        await callback.message.answer("Введите новое имя:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(EditProfileStates.edit_name)
    elif field == "age":
        await callback.message.answer("Введите новый возраст:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(EditProfileStates.edit_age)
    elif field == "city":
        await callback.message.answer("Введите ваш город или отправьте локацию:", reply_markup=get_location_keyboard())
        await state.set_state(EditProfileStates.edit_city)
    elif field == "desc":
        await callback.message.answer("Введите новое описание:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(EditProfileStates.edit_description)
    elif field == "gender":
        await callback.message.answer("Ваш пол?", reply_markup=get_gender_keyboard())
        await state.set_state(EditProfileStates.edit_gender)
    elif field == "looking":
        await callback.message.answer("Кого вы ищете?", reply_markup=get_looking_for_keyboard())
        await state.set_state(EditProfileStates.edit_looking_for)
    elif field == "purpose":
        await callback.message.answer("Ваша цель?", reply_markup=get_purpose_keyboard())
        await state.set_state(EditProfileStates.edit_purpose)
    elif field == "media":
        await callback.message.answer("Отправьте до 5 фото или видео:", reply_markup=get_media_keyboard())
        await state.update_data(media=[])
        await state.set_state(EditProfileStates.edit_media)
        
    await callback.answer()

# Handlers for processing field edits
@router.message(EditProfileStates.edit_name)
async def process_edit_name(message: Message, state: FSMContext):
    await db.update_user_field(message.from_user.id, "name", message.text)
    await state.clear()
    await message.answer("Имя обновлено! ✅", reply_markup=get_main_menu())
    await show_my_profile(message)

@router.message(EditProfileStates.edit_age)
async def process_edit_age(message: Message, state: FSMContext):
    if not message.text.isdigit() or not (14 <= int(message.text) <= 100):
        await message.answer("Пожалуйста, введите корректный возраст (число от 14 до 100).")
        return
    await db.update_user_field(message.from_user.id, "age", int(message.text))
    await state.clear()
    await message.answer("Возраст обновлен! ✅", reply_markup=get_main_menu())
    await show_my_profile(message)

@router.message(EditProfileStates.edit_gender)
async def process_edit_gender(message: Message, state: FSMContext):
    if message.text not in ["Парень", "Девушка"]:
        return
    await db.update_user_field(message.from_user.id, "gender", message.text)
    await state.clear()
    await message.answer("Пол обновлен! ✅", reply_markup=get_main_menu())
    await show_my_profile(message)

@router.message(EditProfileStates.edit_looking_for)
async def process_edit_looking_for(message: Message, state: FSMContext):
    if message.text not in ["Парня", "Девушку", "Всех"]:
        return
    await db.update_user_field(message.from_user.id, "looking_for", message.text)
    await state.clear()
    await message.answer("Предпочтения обновлены! ✅", reply_markup=get_main_menu())
    await show_my_profile(message)

@router.message(EditProfileStates.edit_purpose)
async def process_edit_purpose(message: Message, state: FSMContext):
    await db.update_user_field(message.from_user.id, "purpose", message.text)
    await state.clear()
    await message.answer("Цель обновлена! ✅", reply_markup=get_main_menu())
    await show_my_profile(message)

@router.message(EditProfileStates.edit_city, F.location | F.text)
async def process_edit_city(message: Message, state: FSMContext):
    if message.location:
        city = await get_city_from_coords(message.location.latitude, message.location.longitude)
    else:
        city = message.text.strip().title()
    await db.update_user_field(message.from_user.id, "city", city)
    await state.clear()
    await message.answer(f"Город обновлен на {city}! ✅", reply_markup=get_main_menu())
    await show_my_profile(message)

@router.message(EditProfileStates.edit_description)
async def process_edit_description(message: Message, state: FSMContext):
    await db.update_user_field(message.from_user.id, "description", message.text)
    await state.clear()
    await message.answer("Описание обновлено! ✅", reply_markup=get_main_menu())
    await show_my_profile(message)

@router.message(EditProfileStates.edit_media, F.photo | F.video)
async def process_edit_media_item(message: Message, state: FSMContext):
    data = await state.get_data()
    media_list = data.get("media", [])
    if len(media_list) >= 5:
        return
    file_id = message.photo[-1].file_id if message.photo else message.video.file_id
    file_type = "photo" if message.photo else "video"
    media_list.append({"file_id": file_id, "file_type": file_type})
    await state.update_data(media=media_list)
    await message.answer(f"Загружено {len(media_list)}/5. Отправьте еще или нажмите «Завершить».")

@router.message(EditProfileStates.edit_media, F.text == "✅ Завершить")
async def process_edit_media_done(message: Message, state: FSMContext):
    data = await state.get_data()
    media_list = data.get("media", [])
    if not media_list:
        await message.answer("Загрузите хотя бы одно фото или видео.")
        return
    
    await db.clear_user_media(message.from_user.id)
    main_photo = None
    for m in media_list:
        await db.add_user_media(message.from_user.id, m["file_id"], m["file_type"])
        if m["file_type"] == "photo" and not main_photo:
            main_photo = m["file_id"]
    
    await db.update_user_field(message.from_user.id, "photo", main_photo or media_list[0]["file_id"])
    await state.clear()
    await message.answer("Медиафайлы обновлены! ✅", reply_markup=get_main_menu())
    await show_my_profile(message)

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
