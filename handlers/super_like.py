from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from states.registration import SuperLikeStates
import database.db as db

router = Router()

@router.message(SuperLikeStates.waiting_for_message)
async def process_super_like_message(message: Message, state: FSMContext):
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    from_user_id = message.from_user.id
    
    if not target_user_id:
        await state.clear()
        return

    # Отправляем уведомление
    from_user = await db.get_user(from_user_id)
    try:
        await message.bot.send_message(
            target_user_id,
            f"⭐ <b>СУПЕР-ЛАЙК!</b>\n"
            f"Вы очень понравились пользователю {from_user['name']}!\n\n"
            f"💌 Сообщение: <i>{message.text}</i>\n\n"
            f"Найти анкету можно в разделе 'Кто меня лайкнул'.",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Failed to send super like to {target_user_id}: {e}")

    # Сохраняем лайк в базу
    await db.add_like(from_user_id, target_user_id, True)
    await db.use_super_like(from_user_id)
    
    await state.clear()
    await message.answer("Супер-лайк успешно отправлен! 🚀")
    
    # Показываем следующую анкету
    from handlers.search import show_next_profile
    await show_next_profile(message, from_user_id)
