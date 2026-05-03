import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.db import create_tables
from handlers import registration, search, filters

async def main():
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    # Создание таблиц БД
    await create_tables()
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрация роутеров
    dp.include_router(registration.router)
    dp.include_router(search.router)
    dp.include_router(filters.router)
    
    # Запуск поллинга
    logging.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
