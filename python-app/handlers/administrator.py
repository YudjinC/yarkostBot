from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove

from components import database as db
from components import keyboards as kb
from modules import botStages

from dotenv import load_dotenv
import os

load_dotenv()
admin = int(os.getenv('ADMIN_ID'))


async def promo_codes(message: types.Message):
    await botStages.AdminScreenPlay.admin_promo.set()
    await message.answer(
        f'Вы находитесь в меню управления промокадми.',
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(
        f'Вы можете запросить список промокодов, изменить существующий или добавить новый.',
        reply_markup=kb.promoKeyboardAdmin
    )


async def promo_cancel(message: types.Message):
    await botStages.AdminScreenPlay.admin_start.set()
    await message.answer(
        f'Возвращаеся к основной админ-панели.',
        reply_markup=kb.mainKeyboardAdmin
    )


async def admin_play(message: types.Message):
    await message.answer(
        f'Вы авторизовались как администратор!',
        reply_markup=kb.mainKeyboardAdmin
    )


def register_administrator_handlers(dp: Dispatcher):
    dp.register_message_handler(promo_codes, state=botStages.AdminScreenPlay.admin_start, text=['Промокоды'])
    dp.register_message_handler(promo_cancel, state=botStages.AdminScreenPlay.admin_promo, text=['Отмена'])
    dp.register_message_handler(admin_play, state=botStages.AdminScreenPlay.admin_start)
