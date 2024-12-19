from aiogram import types, Dispatcher
from aiogram.types import ReplyKeyboardRemove

from components import database as db
from components import keyboards as kb
from modules import botStages

from datetime import datetime
import re


async def upload_users_db(message: types.Message):
    pool = await message.bot.get('pg_pool')
    await message.answer(
        f'Начинаю выгрузку БД, дождитесь сообщения!'
    )
    await db.upload_users_database(pool, message.bot, message.chat.id)


async def input_promo_for_upload(message: types.Message):
    await message.answer(
        f'Введите промокод.',
        reply_markup=kb.backwardKeyboard
    )
    await botStages.AdminScreenPlay.admin_upload_with_promo.set()


async def upload_users_db_with_promo(message: types.Message):
    pool = await message.bot.get('pg_pool')
    promo_code = message.text.strip()
    exist = await db.select_one_promo(pool, promo_code)
    if not exist:
        await message.answer(
            f'Промокод с названием "{promo_code}" не найден! Убедитесь, что вы указали верный код.'
        )
        return
    else:
        await message.answer(
            f'Начинаю выгрузку БД',
            reply_markup=ReplyKeyboardRemove()
        )
        await db.upload_users_database_with_promo(pool, message.bot, message.chat.id, promo_code)
        await botStages.AdminScreenPlay.admin_start.set()


async def upload_users_db_with_promo_cancel(message: types.Message):
    await message.answer(
        f'Возвращаемся к основной панели.',
        reply_markup=kb.mainKeyboardAdmin
    )
    await botStages.AdminScreenPlay.admin_start.set()


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
        promos = await db.select_promo(pool)
        if not promos:
            await message.answer(
                f'Нет активных промокодов.'
            )
            return
        promo_list = 'Ваши промокоды:\n'
        for record in promos:
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
        reply_markup=kb.backwardKeyboard
    )


async def promo_add_process(message: types.Message):
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


async def promo_add_process_cancel(message: types.Message):
    await botStages.AdminScreenPlay.admin_promo.set()
    await message.answer(
        f'Возвращаемся к панели промо-кодов.',
        reply_markup=kb.promoKeyboardAdmin
    )


async def promo_change(message: types.Message):
    await botStages.AdminScreenPlay.admin_promo_change.set()
    await message.answer(
        f'Вы хотите изменить существующий промокод.\n'
        f'Для этого введите название промокода, а после НОВЫЕ начальную и конечную даты!\n'
        f'Делать это нужно в след. формате:\n'
        f'promo: (указать код БЕЗ пробелов!)\n'
        f'start: (дата начала в формате YYYY-MM-DD)\n'
        f'end: (дата окончания в формате YYYY-MM-DD)',
        reply_markup=kb.backwardKeyboard
    )


async def promo_change_process(message: types.Message):
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
        exist = await db.select_one_promo(pool, promo_code)
        if not exist:
            await message.answer(
                f'Промокод с названием "{promo_code}" не найден! Убедитесь, что вы указали верный код.'
            )
            return
        await db.update_promo(pool, promo_code, start_date, end_date)
        await message.answer(
            f'Промокод успешно обновлён:\n'
            f'Код: {promo_code}\n'
            f'Дата начала: {start_date}\n'
            f'Дата окончания: {end_date}',
            reply_markup=kb.promoKeyboardAdmin
        )
        await botStages.AdminScreenPlay.admin_promo.set()
    except Exception as e:
        await message.answer(
            f'Произошла ошибка при обновлении промокода: {e}'
        )


async def promo_change_process_cancel(message: types.Message):
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


async def input_message_text(message: types.Message):
    await message.answer(
        f'Вы хотите сделать рассылку для пользователей бота!\n'
        f'Сообщение будет доставлено всем пользователям, у которых активен бот.\n\n'
        f'Первую строку сообщения я отправлю сам в виде "Добрый день, <имя пользователя>!"\n'
        f'А дальше вы:',
        reply_markup=kb.backwardKeyboard
    )
    await botStages.AdminScreenPlay.admin_send_messages.set()


async def send_message_text(message: types.Message):
    pool = await message.bot.get('pg_pool')
    result = await db.select_tg_id_and_gio(pool)
    if not result:
        await message.answer(
            f'Упс, похоже, у нас ещё нет ни одного юзера...\n'
            f'Возвращаю главное меню',
            reply_markup=kb.mainKeyboardAdmin
        )
        await botStages.AdminScreenPlay.admin_start.set()
        return
    for tg_id, fio in result:
        personalized_text = (f'Добрый день, {fio}!\n'
                             f'{message.text}')
        try:
            await message.bot.send_message(tg_id, personalized_text)
        except Exception as e:
            await message.answer(f"Не удалось отправить сообщение пользователю {tg_id}: {e}")


async def send_message_text_cancel(message: types.Message):
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
    dp.register_message_handler(upload_users_db, state=botStages.AdminScreenPlay.admin_start,
                                text=['Выгрузить базу данных пользователей'])
    dp.register_message_handler(input_promo_for_upload, state=botStages.AdminScreenPlay.admin_start,
                                text=['Выгрузить по промокоду'])
    dp.register_message_handler(upload_users_db_with_promo_cancel,
                                state=botStages.AdminScreenPlay.admin_upload_with_promo,
                                text=['Назад'])
    dp.register_message_handler(upload_users_db_with_promo, state=botStages.AdminScreenPlay.admin_upload_with_promo,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(promo_codes, state=botStages.AdminScreenPlay.admin_start, text=['Промокоды'])
    dp.register_message_handler(promo_select, state=botStages.AdminScreenPlay.admin_promo,
                                text=['Вывести список промокодов'])
    dp.register_message_handler(promo_add, state=botStages.AdminScreenPlay.admin_promo, text=['Добавить промокод'])
    dp.register_message_handler(promo_change, state=botStages.AdminScreenPlay.admin_promo, text=['Изменить промокод'])
    dp.register_message_handler(promo_add_process_cancel, state=botStages.AdminScreenPlay.admin_promo_add,
                                text=['Назад'])
    dp.register_message_handler(promo_add_process, state=botStages.AdminScreenPlay.admin_promo_add,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(promo_change_process_cancel, state=botStages.AdminScreenPlay.admin_promo_change,
                                text=['Назад'])
    dp.register_message_handler(promo_change_process, state=botStages.AdminScreenPlay.admin_promo_change,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(promo_cancel, state=botStages.AdminScreenPlay.admin_promo,
                                text=['Назад'])
    dp.register_message_handler(input_message_text, state=botStages.AdminScreenPlay.admin_send_messages,
                                text=['Рассылка'])
    dp.register_message_handler(send_message_text_cancel, state=botStages.AdminScreenPlay.admin_send_messages,
                                text=['Назад'])
    dp.register_message_handler(send_message_text, state=botStages.AdminScreenPlay.admin_send_messages,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(admin_play, state=botStages.AdminScreenPlay.admin_start)
