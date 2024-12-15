from aiogram import types, Dispatcher
from aiogram.types import InputFile

from components import database as db
from components import keyboards as kb
from components import utils
from modules import botStages
from handlers.advanced import advanced_stage
from handlers.administrator import admin_play

from dotenv import load_dotenv
import os

load_dotenv()
admin = int(os.getenv('ADMIN_ID'))


async def cmd_start(message: types.Message):
    if message.from_user.id == admin:
        await botStages.AdminScreenPlay.admin_start.set()
        await admin_play(message)
    else:
        pool = await message.bot.get('pg_pool')
        await db.cmd_start_db(pool, message.from_user.id)
        advanced = await db.check_advanced_state(pool, message.from_user.id)
        if advanced:
            await botStages.UserAdvancedScreenplay.advanced.set()
            await advanced_stage(message)
        else:
            await message.bot.send_photo(
                message.chat.id,
                photo=InputFile('photos/registration.jpg'),
                caption=(
                    f'💖💖 КАК ПОЛУЧИТЬ ПОДАРОК\?\n'
                    f'Все очень просто:\n\n'
                    f'\_ Оставить отзыв о продукте YARKOST на сайте маркетплейса\.\n\n'
                    f'\*каждому участнику гарантированный подарок\! Победителей главных призов определим в @yarkostorganic в прямом эфире\.\n\n'
                    f'{utils.conditionsLink} /\n'
                    f'{utils.supportLink}\n\n'
                    f'Жмите кнопку УЧАСТВУЮ⬇'
                ),
                parse_mode=types.ParseMode.MARKDOWN_V2,
                reply_markup=kb.playerInline
            )


def register_start_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=['start'])
