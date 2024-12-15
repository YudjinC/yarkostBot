from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv

from components import database as db
from components import s3
from handlers import register_handlers

import logging
import os
logging.basicConfig(level=logging.DEBUG)

load_dotenv()
token = os.getenv('TOKEN')

bot = Bot(token)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)


async def on_startup(_):
    pool = await db.create_db_pool()
    bot['pg_pool'] = pool
    await db.db_start(pool)
    await s3.minio_start()
    print('Бот стартовал')
    register_handlers(dp)


async def on_shutdown():
    pool = bot.get('pg_pool')
    if pool:
        await pool.close()
    print("Пул соединений закрыт")

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=True)
