import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_ID
from database.db import create_tables
from handlers import registration, search, filters, admin, vip
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
import database.db as db

class BanMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = None
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
        
        if user_id:
            user = await db.get_user(user_id)
            if user and user['is_banned']:
                if isinstance(event, Message):
                    await event.answer("Вы заблокированы в этом боте. 🚫")
                elif isinstance(event, CallbackQuery):
                    await event.answer("Вы заблокированы. 🚫", show_alert=True)
                return
        
        return await handler(event, data)

async def main():
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    # Создание таблиц БД
    await create_tables()
    
    # Автоматическое назначение админа из конфига
    if ADMIN_ID:
        try:
            await db.set_super_admin_status(int(ADMIN_ID), 1)
            logging.info(f"User {ADMIN_ID} set as SUPER ADMIN from config.")
        except Exception as e:
            logging.error(f"Failed to set super admin {ADMIN_ID}: {e}")
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрация мидлварей
    dp.message.middleware(BanMiddleware())
    dp.callback_query.middleware(BanMiddleware())
    
    # Регистрация роутеров
    dp.include_router(admin.router)
    dp.include_router(registration.router)
    dp.include_router(search.router)
    dp.include_router(filters.router)
    dp.include_router(vip.router)
    
    # Запуск поллинга
    logging.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
