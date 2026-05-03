import os
import logging
from aiogram import Bot
from aiogram.types import FSInputFile
from datetime import datetime

DB_NAME = "dating.db"

# Храним ID сообщений, чтобы удалять старые
# Формат: {"short_1": 12345, "daily_1": 67890}
message_history = {}

async def send_telegram_backup(bot: Bot, admin_id: int, backup_type: str, index: int):
    if not os.path.exists(DB_NAME):
        logging.error("Cannot send backup: DB file does not exist.")
        return False
        
    file_key = f"{backup_type}_{index}"
    filename = f"backup_{index}.db" if backup_type == "short" else f"daily_{index}.db"
    
    file = FSInputFile(DB_NAME, filename=filename)
    caption = f"📦 <b>Автоматический бэкап базы данных</b>\n"
    caption += f"Тип: {'Краткосрочный' if backup_type == 'short' else 'Дневной'} ({index})\n"
    caption += f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    caption += f"<i>Для восстановления отправьте этот файл боту с командой /restore</i>"

    try:
        # Пытаемся удалить старое сообщение с таким же индексом
        if file_key in message_history:
            try:
                await bot.delete_message(chat_id=admin_id, message_id=message_history[file_key])
            except Exception as e:
                logging.warning(f"Could not delete old backup message {file_key}: {e}")
                
        # Отправляем новое сообщение
        msg = await bot.send_document(chat_id=admin_id, document=file, caption=caption, parse_mode="HTML")
        message_history[file_key] = msg.message_id
        logging.info(f"Successfully sent backup {filename} to admin.")
        return True
    except Exception as e:
        logging.error(f"Failed to send backup to admin: {e}")
        return False

async def send_manual_backup(bot: Bot, admin_id: int):
    if not os.path.exists(DB_NAME): return False
    
    file = FSInputFile(DB_NAME, filename="manual_backup.db")
    caption = f"🔄 <b>Ручной бэкап перед перезагрузкой</b>\n"
    caption += f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    try:
        await bot.send_document(chat_id=admin_id, document=file, caption=caption, parse_mode="HTML")
        return True
    except Exception as e:
        logging.error(f"Failed to send manual backup: {e}")
        return False
