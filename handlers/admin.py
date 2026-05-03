from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states.admin import BroadcastStates
import database.db as db
from keyboards.reply import get_main_menu
import asyncio
import logging
import os
import sys
from database import telegram_sync

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
        f"┣ 💎 VIP-юзеров: <b>{stats['vip']}</b>\n"
        f"┣ ✅ Верифицированных: <b>{stats['verified']}</b>\n"
        f"┗ 🚫 Забанено: <b>{stats['banned']}</b>\n\n"
        f"🛠 <b>УПРАВЛЕНИЕ КОМАНДАМИ:</b>\n"
        f"┃\n"
        f"┣ 🚷 <b>Блокировка:</b>\n"
        f"┃ <code>/ban ID</code> | <code>/unban ID</code>\n"
        f"┃\n"
        f"┣ 🧑‍💼 <b>Модераторы:</b>\n"
        f"┃ <code>/setadmin ID</code> | <code>/unsetadmin ID</code>\n"
        f"┃\n"
        f"┣ 💎 <b>VIP & ✅ Верификация:</b>\n"
        f"┃ <code>/setvip ID</code> | <code>/unsetvip ID</code>\n"
        f"┃ <code>/verify ID</code> | <code>/unverify ID</code>\n"
        f"┃\n"
        f"┣ 👑 <b>Главные:</b>\n"
        f"┃ <code>/setsuper ID</code> | <code>/unsetsuper ID</code>\n"
        f"┃\n"
        f"┣ 🔍 <b>Поиск юзера по имени:</b>\n"
        f"┃ <code>/find Имя</code>\n"
        f"┃\n"
        f"┣ 🏆 <b>Топ рефералов:</b>\n"
        f"┃ <code>/topref</code>\n"
        f"┃\n"
        f"┣ 📢 <b>Рассылка всем (Главные):</b>\n"
        f"┃ <code>/broadcast</code>\n"
        f"┃\n"
        f"┣ 🔄 <b>Перезагрузка (Главные):</b>\n"
        f"┃ <code>/restart</code>\n"
        f"┃\n"
        f"┣ 💾 <b>Восстановление БД:</b>\n"
        f"┃ <i>Reply на файл .db с текстом</i> <code>/restore</code>\n"
        f"┃\n"
        f"┗ 🗑 <b>Удаление:</b> (Кнопки в поиске)\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<i>Последнее обновление: {message.date.strftime('%H:%M:%S')}</i>"
    )
    
    await message.answer(text, parse_mode="HTML")

@router.message(Command("setvip"))
async def set_vip(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user or not user['is_admin']: return
    try:
        target_id = int(message.text.split()[1])
        await db.activate_vip(target_id, days=30)
        await message.answer(f"Пользователь {target_id} теперь VIP 💎 (на 30 дней)")
    except (IndexError, ValueError): await message.answer("Использование: /setvip ID")

@router.message(Command("unsetvip"))
async def unset_vip(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user or not user['is_admin']: return
    try:
        target_id = int(message.text.split()[1])
        await db.set_vip_status(target_id, 0)
        await message.answer(f"Пользователь {target_id} больше не VIP")
    except (IndexError, ValueError): await message.answer("Использование: /unsetvip ID")

@router.message(Command("unsetsuper"))
async def unset_super_admin(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user or not user['is_super_admin']: return
    try:
        target_id = int(message.text.split()[1])
        await db.set_super_admin_status(target_id, 0)
        await message.answer(f"Пользователь {target_id} больше не главный админ")
    except (IndexError, ValueError): await message.answer("Использование: /unsetsuper ID")

@router.message(Command("restart"))
async def restart_bot(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user or not user['is_super_admin']: 
        await message.answer("Эта команда доступна только Главным админам.")
        return
        
    await message.answer("⏳ Создаю ручной бэкап базы данных перед перезагрузкой...")
    await telegram_sync.send_manual_backup(message.bot, message.from_user.id)
    await message.answer("✅ Бэкап отправлен в этот чат. Перезагружаюсь...")

    await asyncio.sleep(1)
    os.execv(sys.executable, ['python'] + sys.argv)

@router.message(Command("restore"))
async def restore_db(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user or not user['is_super_admin']: return
    
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.answer("⚠️ Пожалуйста, сделайте Reply (Ответить) на сообщение с файлом базы данных (backup_X.db) и напишите /restore.")
        return
        
    doc = message.reply_to_message.document
    if not doc.file_name.endswith('.db'):
        await message.answer("⚠️ Это не файл базы данных (.db).")
        return
        
    await message.answer("⏳ Скачиваю и устанавливаю новую базу данных...")
    try:
        file_info = await message.bot.get_file(doc.file_id)
        await message.bot.download_file(file_info.file_path, "dating.db")
        await message.answer("✅ База данных успешно восстановлена! Перезагружаюсь для применения изменений...")
        await asyncio.sleep(1)
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при загрузке файла: {e}")

@router.message(Command("find"))
async def find_user_by_name(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user or not user['is_admin']: return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /find [Имя]")
        return
        
    search_query = args[1]
    users = await db.get_users_by_name(search_query)
    
    if not users:
        await message.answer("Пользователи не найдены. 😕")
        return
        
    text = f"🔍 <b>Результаты поиска '{search_query}':</b>\n\n"
    for u in users:
        username = f" (@{u['username']})" if u['username'] else ""
        text += f"👤 {u['name']}{username} - ID: <code>{u['id']}</code>\n"
        
    await message.answer(text, parse_mode="HTML")

@router.message(Command("topref"))
async def top_referrers(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user or not user['is_admin']: return
    
    top = await db.get_top_referrers(limit=15)
    
    if not top:
        await message.answer("Пока нет пользователей, пригласивших кого-либо. 😕")
        return
        
    text = "🏆 <b>Топ рефералов (агенты влияния):</b>\n\n"
    for i, u in enumerate(top, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} <b>{u['name']}</b> (<code>{u['id']}</code>) - пригласил: <b>{u['referrals_count']}</b>\n"
        
    await message.answer(text, parse_mode="HTML")

@router.message(Command("broadcast"))
async def start_broadcast(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user or not user['is_super_admin']: 
        await message.answer("Эта команда доступна только Главным админами.")
        return
        
    await message.answer(
        "📢 <b>Режим массовой рассылки</b>\n\n"
        "Отправьте сообщение (текст, фото, видео), которое нужно разослать всем пользователям бота.\n"
        "Для отмены напишите 'отмена'.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    await state.set_state(BroadcastStates.waiting_for_message)

@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast(message: Message, state: FSMContext):
    if message.text and message.text.lower() == 'отмена':
        await state.clear()
        await message.answer("Рассылка отменена.", reply_markup=get_main_menu())
        return

    all_user_ids = await db.get_all_user_ids()
    await message.answer(f"⏳ Начинаю рассылку для {len(all_user_ids)} пользователей...", reply_markup=get_main_menu())
    await state.clear()
    
    success_count = 0
    fail_count = 0
    
    # Запускаем в фоне, чтобы не блокировать обработку других сообщений
    asyncio.create_task(run_broadcast(message, all_user_ids))
    await message.answer("Рассылка запущена в фоновом режиме. Вы получите уведомление по завершении.")

async def run_broadcast(message: Message, user_ids: list):
    success_count = 0
    fail_count = 0
    
    for uid in user_ids:
        try:
            await message.copy_to(uid)
            success_count += 1
            await asyncio.sleep(0.05)  # Telegram limits: 30 messages per second roughly
        except Exception as e:
            fail_count += 1
            logging.error(f"Failed to send broadcast to {uid}: {e}")
            
    try:
        await message.bot.send_message(
            message.from_user.id,
            f"✅ <b>Рассылка завершена!</b>\n\n"
            f"Успешно отправлено: <b>{success_count}</b>\n"
            f"Не удалось (заблокировали бота и т.д.): <b>{fail_count}</b>",
            parse_mode="HTML"
        )
    except:
        pass

@router.message(Command("verify"))
async def verify_user(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user or not user['is_admin']: return
    try:
        target_id = int(message.text.split()[1])
        await db.set_verified_status(target_id, 1)
        await message.answer(f"Пользователь {target_id} верифицирован ✅")
    except (IndexError, ValueError): await message.answer("Использование: /verify ID")

@router.message(Command("unverify"))
async def unverify_user(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user or not user['is_admin']: return
    try:
        target_id = int(message.text.split()[1])
        await db.set_verified_status(target_id, 0)
        await message.answer(f"Пользователь {target_id} больше не верифицирован")
    except (IndexError, ValueError): await message.answer("Использование: /unverify ID")

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
