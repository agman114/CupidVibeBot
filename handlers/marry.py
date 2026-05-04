from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command
import database.db as db

router = Router()

@router.message(Command("divorce"))
async def divorce_command(message: Message):
    user_id = message.from_user.id
    spouse_id = await db.get_spouse(user_id)
    
    if not spouse_id:
        await message.answer("Вы не состоите в браке! 🕊️")
        return
        
    await db.remove_marriage(user_id)
    await message.answer("💔 Вы успешно развелись. Теперь вы снова свободны!")
    
    # Пытаемся уведомить второго супруга, если это возможно
    try:
        await message.bot.send_message(spouse_id, "💔 Ваш супруг(а) подал(а) на развод. Теперь вы свободны.")
    except Exception:
        pass
