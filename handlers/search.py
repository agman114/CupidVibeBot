from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards.inline import get_swipe_keyboard, get_liker_swipe_keyboard
import database.db as db

router = Router()

async def show_next_profile(message: Message, user_id: int):
    target_user = await db.get_next_user(user_id)
    if not target_user:
        await message.answer("На данный момент новых анкет нет. Попробуйте позже! 😔")
        return

    caption = f"{target_user['name']}, {target_user['age']}, {target_user['city']}\nЦель: {target_user['purpose']}\n\n{target_user['description']}"
    await message.answer_photo(
        photo=target_user['photo'],
        caption=caption,
        reply_markup=get_swipe_keyboard(target_user['id'])
    )

async def show_next_liker(message: Message, user_id: int):
    target_user = await db.get_next_liker(user_id)
    if not target_user:
        await message.answer("Больше никто не лайкнул вашу анкету. 😔")
        return

    caption = f"Вы понравились этому человеку! ❤️\n\n{target_user['name']}, {target_user['age']}, {target_user['city']}\nЦель: {target_user['purpose']}\n\n{target_user['description']}"
    await message.answer_photo(
        photo=target_user['photo'],
        caption=caption,
        reply_markup=get_liker_swipe_keyboard(target_user['id'])
    )

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
async def process_swipe(callback: CallbackQuery):
    action, target_user_id_str = callback.data.replace("swipe_", "").split("_")
    target_user_id = int(target_user_id_str)
    from_user_id = callback.from_user.id

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
async def show_matches(message: Message):
    matches = await db.get_matches(message.from_user.id)
    if not matches:
        await message.answer("У вас пока нет взаимных симпатий. Продолжайте искать! ❤️")
        return

    await message.answer(f"У вас {len(matches)} взаимных симпатий! 💞")
    
    for match in matches:
        match_dict = dict(match)
        if match_dict.get('username'):
            link = f"https://t.me/{match_dict['username']}"
        else:
            link = f"tg://user?id={match_dict['id']}"
            
        caption = f"<b>{match_dict['name']}, {match_dict['age']}</b>, {match_dict['city']}\n\n<a href='{link}'>Написать {match_dict['name']} 💌</a>"
        await message.answer_photo(
            photo=match_dict['photo'],
            caption=caption,
            parse_mode="HTML"
        )
