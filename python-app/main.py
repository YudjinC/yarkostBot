from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv

from components import database as db
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
    await db.db_start()
    print('Бот стартовал')

register_handlers(dp)

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
