from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import database.db as db

router = Router()

@router.message(F.text == "💎 VIP-статус")
async def show_vip_info(message: Message):
    user = await db.get_user(message.from_user.id)
    
    status = "АКТИВЕН ✅" if user and user['is_vip'] else "НЕ АКТИВЕН ❌"
    
    text = (
        f"<b>💎 ПРЕИМУЩЕСТВА VIP-СТАТУСА:</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👑 <b>Особый значок в профиле</b>\n"
        f"<i>Вы будете выделяться в ленте, что повышает количество лайков.</i>\n\n"
        f"🚀 <b>Приоритетный показ</b>\n"
        f"<i>Ваша анкета будет показываться чаще другим пользователям.</i>\n\n"
        f"👀 <b>Видеть всех, кто вас лайкнул</b>\n"
        f"<i>(В будущих обновлениях)</i>\n\n"
        f"♾ <b>Безлимитные лайки</b>\n"
        f"<i>Никаких ограничений на поиск!</i>\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Ваш статус: {status}</b>\n\n"
        f"Чтобы приобрести VIP или верифицировать профиль ✅, напишите нашему администратору!"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать администратору", url="https://t.me/your_admin_username")]
        ]
    )
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
