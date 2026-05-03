from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.inline import get_swipe_keyboard, get_liker_swipe_keyboard, get_matches_keyboard
from states.registration import SuperLikeStates
import database.db as db

router = Router()

async def show_next_profile(message: Message, user_id: int):
    target_user = await db.get_next_user(user_id)
    if not target_user:
        await message.answer("На данный момент новых анкет нет. Попробуйте позже! 😔")
        return

    current_user = await db.get_user(user_id)
    is_admin = bool(current_user and current_user['is_admin'])
    is_vip = bool(current_user and current_user['is_vip'])

    media = await db.get_user_media(target_user['id'])
    
    name_str = f"<b>{target_user['name']}</b>"
    if target_user['is_vip']: name_str += " 💎"
    if target_user['is_verified']: name_str += " ✅"
    
    caption = f"{name_str}, {target_user['age']}, {target_user['city']}\nЦель: {target_user['purpose']}\n\n{target_user['description']}"
    
    if is_admin:
        caption += f"\n\n🆔 ID: <code>{target_user['id']}</code>"

    if not media:
        await message.answer_photo(
            photo=target_user['photo'],
            caption=caption,
            reply_markup=get_swipe_keyboard(target_user['id'], is_admin=is_admin, is_vip=is_vip),
            parse_mode="HTML"
        )
    elif len(media) == 1:
        m = media[0]
        if m['file_type'] == 'photo':
            await message.answer_photo(photo=m['file_id'], caption=caption, reply_markup=get_swipe_keyboard(target_user['id'], is_admin=is_admin, is_vip=is_vip), parse_mode="HTML")
        else:
            await message.answer_video(video=m['file_id'], caption=caption, reply_markup=get_swipe_keyboard(target_user['id'], is_admin=is_admin, is_vip=is_vip), parse_mode="HTML")
    else:
        from aiogram.types import InputMediaPhoto, InputMediaVideo
        media_group = []
        for i, m in enumerate(media):
            if m['file_type'] == 'photo':
                media_group.append(InputMediaPhoto(media=m['file_id'], caption=caption if i == 0 else None, parse_mode="HTML"))
            else:
                media_group.append(InputMediaVideo(media=m['file_id'], caption=caption if i == 0 else None, parse_mode="HTML"))
        
        await message.answer_media_group(media=media_group)
        await message.answer("Вам нравится эта анкета?", reply_markup=get_swipe_keyboard(target_user['id'], is_admin=is_admin, is_vip=is_vip))

async def show_next_liker(message: Message, user_id: int):
    target_user = await db.get_next_liker(user_id)
    if not target_user:
        await message.answer("Больше никто не лайкнул вашу анкету. 😔")
        return

    current_user = await db.get_user(user_id)
    is_admin = bool(current_user and current_user['is_admin'])

    media = await db.get_user_media(target_user['id'])
    
    name_str = f"<b>{target_user['name']}</b>"
    if target_user['is_vip']: name_str += " 💎"
    if target_user['is_verified']: name_str += " ✅"

    caption = f"Вы понравились этому человеку! ❤️\n\n{name_str}, {target_user['age']}, {target_user['city']}\nЦель: {target_user['purpose']}\n\n{target_user['description']}"
    
    if is_admin:
        caption += f"\n\n🆔 ID: <code>{target_user['id']}</code>"

    if not media:
        await message.answer_photo(
            photo=target_user['photo'],
            caption=caption,
            reply_markup=get_liker_swipe_keyboard(target_user['id'], is_admin=is_admin),
            parse_mode="HTML"
        )
    elif len(media) == 1:
        m = media[0]
        if m['file_type'] == 'photo':
            await message.answer_photo(photo=m['file_id'], caption=caption, reply_markup=get_liker_swipe_keyboard(target_user['id'], is_admin=is_admin), parse_mode="HTML")
        else:
            await message.answer_video(video=m['file_id'], caption=caption, reply_markup=get_liker_swipe_keyboard(target_user['id'], is_admin=is_admin), parse_mode="HTML")
    else:
        from aiogram.types import InputMediaPhoto, InputMediaVideo
        media_group = []
        for i, m in enumerate(media):
            if m['file_type'] == 'photo':
                media_group.append(InputMediaPhoto(media=m['file_id'], caption=caption if i == 0 else None, parse_mode="HTML"))
            else:
                media_group.append(InputMediaVideo(media=m['file_id'], caption=caption if i == 0 else None, parse_mode="HTML"))
        
        await message.answer_media_group(media=media_group)
        await message.answer("Вы хотите ответить взаимностью?", reply_markup=get_liker_swipe_keyboard(target_user['id'], is_admin=is_admin))

@router.message(F.text == "❤️ Смотреть анкеты")
async def start_search(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала необходимо зарегистрироваться. Нажмите /start")
        return
    await show_next_profile(message, message.from_user.id)

@router.message(F.text == "🙏 Кто меня лайкнул")
async def start_likers_search(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала необходимо зарегистрироваться. Нажмите /start")
        return
    await show_next_liker(message, message.from_user.id)

@router.callback_query(F.data.startswith("swipe_"))
async def process_swipe(callback: CallbackQuery, state: FSMContext = None):
    data_parts = callback.data.replace("swipe_", "").split("_")
    action = data_parts[0]
    target_user_id = int(data_parts[1])
    from_user_id = callback.from_user.id

    if action == "super":
        remaining = await db.get_super_likes_remaining(from_user_id)
        if remaining <= 0:
            await callback.answer("У вас закончились супер-лайки на этой неделе! 😔", show_alert=True)
            return
        
        # Переходим к вводу сообщения
        await state.update_data(target_user_id=target_user_id)
        await callback.message.answer("Введите сообщение для супер-лайка (оно будет доставлено мгновенно):")
        await state.set_state(SuperLikeStates.waiting_for_message)
        await callback.answer()
        return

    is_like = (action == "like")
    
    # Сохраняем действие
    await db.add_like(from_user_id, target_user_id, is_like)

    # Проверяем на взаимность, если это лайк
    if is_like:
        is_match = await db.check_match(from_user_id, target_user_id)
        if is_match:
            # Получаем данные обоих пользователей для уведомления
            from_user = await db.get_user(from_user_id)
            target_user = await db.get_user(target_user_id)
            
            # Уведомляем того, кого лайкнули
            try:
                await callback.bot.send_message(
                    target_user_id,
                    f"Взаимная симпатия! 🎉\n{from_user['name']} ответил(а) взаимностью. Напиши: <a href='tg://user?id={from_user_id}'>{from_user['name']}</a>",
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Failed to notify user {target_user_id}: {e}")
                
            # Уведомляем того, кто лайкнул (текущего)
            await callback.message.answer(
                f"Взаимная симпатия! 🎉\nВы понравились {target_user['name']}. Напиши: <a href='tg://user?id={target_user_id}'>{target_user['name']}</a>",
                parse_mode="HTML"
            )
        else:
            # Просто лайк, уведомляем пользователя
            try:
                await callback.bot.send_message(
                    target_user_id,
                    "Ты кому-то понравился! 🙏 Загляни в раздел 'Кто меня лайкнул', чтобы узнать кто это."
                )
            except Exception as e:
                print(f"Failed to notify user {target_user_id} about like: {e}")

    # Удаляем текущее сообщение (чтобы не спамить в чате)
    await callback.message.delete()
    
    # Показываем следующую анкету
    await show_next_profile(callback.message, from_user_id)
    await callback.answer()

@router.callback_query(F.data.startswith("likerswipe_"))
async def process_liker_swipe(callback: CallbackQuery):
    action, target_user_id_str = callback.data.replace("likerswipe_", "").split("_")
    target_user_id = int(target_user_id_str)
    from_user_id = callback.from_user.id

    is_like = (action == "like")
    await db.add_like(from_user_id, target_user_id, is_like)

    if is_like:
        # Так как этот человек нас УЖЕ лайкнул, это 100% мэтч
        from_user = await db.get_user(from_user_id)
        target_user = await db.get_user(target_user_id)
        
        try:
            await callback.bot.send_message(
                target_user_id,
                f"Взаимная симпатия! 🎉\n{from_user['name']} ответил(а) взаимностью. Напиши: <a href='tg://user?id={from_user_id}'>{from_user['name']}</a>",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Failed to notify user {target_user_id}: {e}")
            
        await callback.message.answer(
            f"Взаимная симпатия! 🎉\nВы понравились {target_user['name']}. Напиши: <a href='tg://user?id={target_user_id}'>{target_user['name']}</a>",
            parse_mode="HTML"
        )

    await callback.message.delete()
    await show_next_liker(callback.message, from_user_id)
    await callback.answer()

@router.message(F.text == "💞 Взаимности")
async def show_matches(message: Message, page: int = 0):
    user_id = message.from_user.id
    matches = await db.get_matches(user_id)
    
    if not matches:
        await message.answer("У вас пока нет взаимных симпатий. Продолжайте искать! ❤️")
        return

    items_per_page = 5
    total_pages = (len(matches) + items_per_page - 1) // items_per_page
    
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    matches_on_page = matches[start_idx:end_idx]
    
    text = f"У вас {len(matches)} взаимных симпатий! 💞\n"
    text += f"Страница {page + 1} из {total_pages}\n\n"
    text += "Нажмите на имя, чтобы написать человеку:"
    
    await message.answer(
        text,
        reply_markup=get_matches_keyboard(matches_on_page, page, total_pages),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("matches_page_"))
async def process_match_pagination(callback: CallbackQuery):
    page = int(callback.data.replace("matches_page_", ""))
    user_id = callback.from_user.id
    matches = await db.get_matches(user_id)
    
    if not matches:
        await callback.message.edit_text("У вас пока нет взаимных симпатий. ❤️")
        return

    items_per_page = 5
    total_pages = (len(matches) + items_per_page - 1) // items_per_page
    
    # Защита от выхода за границы
    if page >= total_pages: page = total_pages - 1
    if page < 0: page = 0
    
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    matches_on_page = matches[start_idx:end_idx]
    
    text = f"У вас {len(matches)} взаимных симпатий! 💞\n"
    text += f"Страница {page + 1} из {total_pages}\n\n"
    text += "Нажмите на имя, чтобы написать человеку:"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_matches_keyboard(matches_on_page, page, total_pages),
        parse_mode="HTML"
    )
    await callback.answer()
