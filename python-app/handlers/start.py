from aiogram import types, Dispatcher
from aiogram.types import InputFile

from components import database as db
from components import keyboards as kb
from components import utils
from modules import botStages
from handlers.advanced import advanced_stage
from handlers.administrator import admin_play


async def cmd_start(message: types.Message):
    pool = await message.bot.get('pg_pool')
    if await db.is_admin_user(pool,message.from_user.id):
        await botStages.AdminScreenPlay.admin_start.set()
        await admin_play(message)
    else:
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
                    f'\*каждому участнику гарантированный подарок\! Победителей главного приза IPHONE '
                    f'и других ценных призов определим 05\.10\.2025 в @yarkostorganic в прямом эфире\.\n\n'
                    f'Жмите кнопку УЧАСТВУЮ⬇'
                ),
                parse_mode=types.ParseMode.MARKDOWN_V2,
                reply_markup=kb.playerInline
            )


def register_start_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=['start'])
