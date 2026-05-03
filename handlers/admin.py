from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import database.db as db
from keyboards.reply import get_main_menu

router = Router()

@router.message(Command("admin"))
async def admin_panel(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user or not user['is_admin']:
        return

    stats = await db.get_detailed_stats()
    total_users = await db.get_all_users_count()
    
    role_icon = "👑" if user['is_super_admin'] else "🛡️"
    role_name = "Главный админ" if user['is_super_admin'] else "Администратор"
    
    men = stats['gender'].get('Парень', 0)
    women = stats['gender'].get('Девушка', 0)
    
    text = (
        f"<b>{role_icon} ПАНЕЛЬ УПРАВЛЕНИЯ {role_icon}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>Ваш статус:</b> <code>{role_name}</code>\n"
        f"🆔 <b>Ваш ID:</b> <code>{message.from_user.id}</code>\n\n"
        f"📊 <b>СТАТИСТИКА БОТА:</b>\n"
        f"┣ 👥 Всего юзеров: <b>{total_users}</b>\n"
        f"┣ 👨 Парней: <b>{men}</b>\n"
        f"┣ 👩 Девушек: <b>{women}</b>\n"
        f"┣ ❤️ Всего мэтчей: <b>{stats['matches']}</b>\n"
        f"┗ 🚫 Забанено: <b>{stats['banned']}</b>\n\n"
        f"🛠 <b>УПРАВЛЕНИЕ КОМАНДАМИ:</b>\n"
        f"┃\n"
        f"┣ 🚷 <b>Блокировка:</b>\n"
        f"┃ <code>/ban ID</code> — Забанить\n"
        f"┃ <code>/unban ID</code> — Разбанить\n"
        f"┃\n"
        f"┣ 🧑‍💼 <b>Модераторы:</b>\n"
        f"┃ <code>/setadmin ID</code> — Назначить\n"
        f"┃ <code>/unsetadmin ID</code> — Снять\n"
        f"┃\n"
        f"┣ 💎 <b>Главные:</b>\n"
        f"┃ <code>/setsuper ID</code> — Назначить\n"
        f"┃ <code>/unsetsuper ID</code> — Снять\n"
        f"┃\n"
        f"┗ 🗑 <b>Удаление:</b>\n"
        f"  (Используйте кнопки в поиске)\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<i>Последнее обновление: {message.date.strftime('%H:%M:%S')}</i>"
    )
    
    await message.answer(text, parse_mode="HTML")

@router.message(Command("setadmin"))
async def set_admin(message: Message):
    current_user = await db.get_user(message.from_user.id)
    if not current_user or not current_user['is_super_admin']:
        await message.answer("Эта команда доступна только Главным админам. 🚫")
        return

    try:
        target_id = int(message.text.split()[1])
        await db.set_admin_status(target_id, 1)
        await message.answer(f"Пользователь {target_id} назначен администратором. ✅")
    except (IndexError, ValueError):
        await message.answer("Использование: /setadmin ID")

@router.message(Command("unsetadmin"))
async def unset_admin(message: Message):
    current_user = await db.get_user(message.from_user.id)
    if not current_user or not current_user['is_super_admin']:
        await message.answer("Эта команда доступна только Главным админам. 🚫")
        return

    try:
        target_id = int(message.text.split()[1])
        target_user = await db.get_user(target_id)
        
        if target_user and target_user['is_super_admin']:
            await message.answer("Невозможно снять права с Главного администратора! ⛔")
            return
            
        await db.set_admin_status(target_id, 0)
        await message.answer(f"Пользователь {target_id} больше не администратор. ❌")
    except (IndexError, ValueError):
        await message.answer("Использование: /unsetadmin ID")

@router.message(Command("setsuper"))
async def set_super(message: Message):
    current_user = await db.get_user(message.from_user.id)
    if not current_user or not current_user['is_super_admin']:
        return

    try:
        target_id = int(message.text.split()[1])
        await db.set_super_admin_status(target_id, 1)
        await message.answer(f"Пользователь {target_id} теперь ГЛАВНЫЙ АДМИН. 👑")
    except (IndexError, ValueError):
        await message.answer("Использование: /setsuper ID")

@router.message(Command("unsetsuper"))
async def unset_super(message: Message):
    current_user = await db.get_user(message.from_user.id)
    if not current_user or not current_user['is_super_admin']:
        return
    
    try:
        target_id = int(message.text.split()[1])
        # Запрещаем снимать супер-админа с самого себя, если он единственный (или просто для безопасности)
        if target_id == message.from_user.id:
            await message.answer("Вы не можете снять права с самого себя! ⚠️")
            return
            
        await db.set_super_admin_status(target_id, 0)
        await message.answer(f"Пользователь {target_id} больше не Главный админ. 📉")
    except (IndexError, ValueError):
        await message.answer("Использование: /unsetsuper ID")

@router.message(Command("ban"))
async def ban_command(message: Message):
    current_user = await db.get_user(message.from_user.id)
    if not current_user or not current_user['is_admin']:
        return

    try:
        target_id = int(message.text.split()[1])
        target_user = await db.get_user(target_id)
        
        if target_user and (target_user['is_super_admin'] or target_user['is_admin']):
            await message.answer("Вы не можете забанить другого администратора! ⛔")
            return
            
        await db.set_ban_status(target_id, 1)
        await message.answer(f"Пользователь {target_id} заблокирован. 🚫")
    except (IndexError, ValueError):
        await message.answer("Использование: /ban ID")

@router.message(Command("unban"))
async def unban_command(message: Message):
    current_user = await db.get_user(message.from_user.id)
    if not current_user or not current_user['is_admin']:
        return

    try:
        target_id = int(message.text.split()[1])
        await db.set_ban_status(target_id, 0)
        await message.answer(f"Пользователь {target_id} разблокирован. ✅")
    except (IndexError, ValueError):
        await message.answer("Использование: /unban ID")

@router.callback_query(F.data.startswith("admin_ban_"))
async def admin_ban_user(callback: CallbackQuery):
    current_user = await db.get_user(callback.from_user.id)
    if not current_user or not current_user['is_admin']:
        await callback.answer("У вас нет прав. 🚫")
        return

    target_id = int(callback.data.replace("admin_ban_", ""))
    target_user = await db.get_user(target_id)
    
    if target_user and (target_user['is_super_admin'] or target_user['is_admin']):
        await callback.answer("Невозможно забанить администратора! ⛔", show_alert=True)
        return

    await db.set_ban_status(target_id, 1)
    await callback.message.answer(f"Пользователь {target_id} заблокирован. 🚫")
    await callback.answer("Пользователь забанен.")

@router.callback_query(F.data.startswith("admin_delete_"))
async def admin_delete_user(callback: CallbackQuery):
    current_user = await db.get_user(callback.from_user.id)
    if not current_user or not current_user['is_admin']:
        await callback.answer("У вас нет прав. 🚫")
        return

    target_id = int(callback.data.replace("admin_delete_", ""))
    target_user = await db.get_user(target_id)
    
    if target_user and (target_user['is_super_admin'] or target_user['is_admin']):
        await callback.answer("Невозможно удалить анкету администратора! ⛔", show_alert=True)
        return

    await db.delete_user(target_id)
    await callback.message.answer(f"Анкета {target_id} удалена. 🗑️")
    await callback.answer("Анкета удалена.")
