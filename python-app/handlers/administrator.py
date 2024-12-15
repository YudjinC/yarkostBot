from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove

from components import database as db
from components import keyboards as kb
from modules import botStages

from dotenv import load_dotenv
from datetime import datetime
import os
import re

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


async def promo_select(message: types.Message):
    pool = await message.bot.get('pg_pool')
    try:
        promo_codes = await db.select_promo(pool)
        if not promo_codes:
            await message.answer(
                f'Нет активных промокодов.'
            )
        else:
            promo_list = 'Ваши промокоды:\n'
            for record in promo_codes:
                promo_list += f"{record['code']}: {record['start_date']}, {record['end_date']}\n"
            await message.answer(promo_list)
    except Exception as e:
        await message.answer(
            f'Произошла ошибка при получении списка промокодов: {e}'
        )


async def promo_add(message: types.Message):
    await botStages.AdminScreenPlay.admin_promo_add.set()
    await message.answer(
        f'При добавлении промокода используейте следующий формат:\n'
        f'promo: (указать код БЕЗ пробелов!)\n'
        f'start: (дата начала в формате YYYY-MM-DD)\n'
        f'end: (дата окончания в формате YYYY-MM-DD)',
        reply_markup=kb.cancelKeyboard
    )


async def process_promo(message: types.Message, state: FSMContext):
    pool = await message.bot.get('pg_pool')
    promo_pattern = (
        r"promo:\s*(?P<promo>[^\s]+)\n"
        r"start:\s*(?P<start>\d{4}-\d{2}-\d{2})\n"
        r"end:\s*(?P<end>\d{4}-\d{2}-\d{2})"
    )
    match = re.fullmatch(promo_pattern, message.text.strip())
    if not match:
        await message.answer(
            f'Неверный формат данных. Убедитесь, что всё соответствует инструкции:\n'
            f'promo: (указать код БЕЗ пробелов!)\n'
            f'start: (дата начала в формате YYYY-MM-DD)\n'
            f'end: (дата окончания в формате YYYY-MM-DD)'
        )
        return
    promo_data = match.groupdict()
    promo_code = promo_data["promo"]
    start_date = promo_data["start"]
    end_date = promo_data["end"]
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        if start_date >= end_date:
            await message.answer(
                f'Дата начала действия промокода должна быть раньше даты окончания.'
            )
            return
    except ValueError:
        await message.answer(
            f'Неверный формат дат. Используйте формат YYYY-MM-DD.'
        )
        return
    try:
        await db.add_promo(pool, promo_code, start_date, end_date)
        await message.answer(
            f'Промокод успешно добавлен:\n'
            f'Код: {promo_code}\n'
            f'Дата начала: {start_date}\n'
            f'Дата окончания: {end_date}',
            reply_markup=kb.promoKeyboardAdmin
        )
        await botStages.AdminScreenPlay.admin_promo.set()
    except Exception as e:
        await message.answer(
            f'Произошла ошибка при сохранении промокода: {e}'
        )


async def promo_add_cancel(message: types.Message):
    await botStages.AdminScreenPlay.admin_promo.set()
    await message.answer(
        f'Возвращаемся к панели промо-кодов.',
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
    dp.register_message_handler(promo_select, state=botStages.AdminScreenPlay.admin_promo, text=['Вывести список промокодов'])
    dp.register_message_handler(promo_add, state=botStages.AdminScreenPlay.admin_promo, text=['Добавить промокод'])
    dp.register_message_handler(promo_add_cancel, state=botStages.AdminScreenPlay.admin_promo_add, text=['Назад'])
    dp.register_message_handler(process_promo, state=botStages.AdminScreenPlay.admin_promo_add)
    dp.register_message_handler(promo_cancel, state=botStages.AdminScreenPlay.admin_promo, text=['Назад'])
    dp.register_message_handler(admin_play, state=botStages.AdminScreenPlay.admin_start)
