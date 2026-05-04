import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

from config import BOT_TOKEN, ADMIN_ID
from database.db import create_tables
from database import telegram_sync
from handlers import registration, search, filters, admin, vip, payments, super_like, inline, marry
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

async def handle_render_health_check(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_render_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server started on port {port} for Render health checks.")

async def short_term_backup_task(bot: Bot, admin_id: int):
    index = 1
    while True:
        await asyncio.sleep(1800)  # 30 минут
        await telegram_sync.send_telegram_backup(bot, admin_id, "short", index)
        index = index + 1 if index < 5 else 1

async def daily_backup_task(bot: Bot, admin_id):
    index = 1
    while True:
        await asyncio.sleep(86400)  # 24 часа
        await telegram_sync.send_telegram_backup(bot, admin_id, "daily", index)
        index = index + 1 if index < 3 else 1

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
    dp.include_router(payments.router)
    dp.include_router(super_like.router)
    dp.include_router(inline.router)
    dp.include_router(marry.router)
    # Запуск веб-сервера для Render (чтобы сервис не отключался)
    asyncio.create_task(start_web_server())

    # Запуск задач резервного копирования
    if ADMIN_ID:
        try:
            admin_id_int = int(ADMIN_ID)
            asyncio.create_task(short_term_backup_task(bot, admin_id_int))
            asyncio.create_task(daily_backup_task(bot, admin_id_int))
        except ValueError:
            logging.error("ADMIN_ID is not an integer. Backups won't start.")


    # Запуск поллинга
    logging.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
