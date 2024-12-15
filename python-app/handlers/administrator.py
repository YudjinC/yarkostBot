from aiogram import types, Dispatcher

from components import database as db
from components import keyboards as kb
from modules import botStages

from dotenv import load_dotenv
import os

load_dotenv()
admin = int(os.getenv('ADMIN_ID'))


async def admin_play(message: types.Message):
    await message.answer(
        f'Вы авторизовались как администратор!',
        reply_markup=kb.mainKeyboardAdmin
    )


def register_administrator_handlers(dp: Dispatcher):
    dp.register_message_handler(admin_play, state=botStages.AminScreenPlay.admin_start)
