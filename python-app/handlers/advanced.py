import asyncio

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InputFile
from aiogram.types import ReplyKeyboardRemove

from components import database as db
from components import keyboards as kb
from components import s3
from modules import botStages

import logging
import random
import string
import re

PROMO_PATTERN = r'^[a-zA-Zа-яА-Я0-9]+$'

MAX_PHOTOS = 2
user_shared_data = {}
state_lock = asyncio.Lock()


async def personal_account(message: types.Message):
    pool = await message.bot.get('pg_pool')
    personal_account_data = await db.personal_account(pool, message.from_user.id)
    if personal_account_data is None:
        await message.answer(
            f'Данные не найдены. Мы обновили базу для следующего конкурса, '
            f'попробуйте зарегестрировать новый купон.'
            )
        return
    await message.answer(
        f'{personal_account_data["fio"]}, это ваш личный кабинет!\n\n'
        f'Номера ваших счастливых билетиков:\n'
        f'{personal_account_data["tickets"]}\n'
        f'Следи за результатами в группе @yarkostorganic !'
    )


async def additional_play(message: types.Message):
    await message.answer(
        f'Выберите купленный товар и нажмите на кнопку!',
        reply_markup=kb.productKeyboard
    )
    await botStages.UserAdvancedScreenplay.advanced_product.set()


async def additional_product(message: types.Message,  state: FSMContext):
    async with state.proxy() as data:
        data['product'] = message.text
    await message.answer(
        f'Покупали на маркетплейсе или на маркет?',
        reply_markup=kb.purchaseLocationKeyboard
    )
    await botStages.UserAdvancedScreenplay.next()


async def additional_purchase_location(message: types.Message, state: FSMContext):
    purchase_location = message.text
    async with state.proxy() as data:
        data['purchase_location'] = purchase_location
    if purchase_location == 'Маркет':
        await message.answer(
            f'Введите, пожалуйста, промокод 💗\n'
            f'Это должно быть одно слово без пробелов!!',
            reply_markup=kb.cancelKeyboard
        )
        await botStages.UserAdvancedScreenplay.advanced_promo.set()
    elif purchase_location == 'Маркетплейс':
        await message.bot.send_photo(
            message.chat.id,
            photo=InputFile('photos/marketplaces.jpg'),
            caption=f'💖 Оставьте честный отзыв о спрей-гидролат от YARKOST\n'
                    f'📎Прикрепите здесь 2 скрина:\n'
                    f'чек об оплате с маркетплейса и отзыв с артикулом товара, '
                    f'воспользовавшись скрепкой около клавиатуры.',
            reply_markup=kb.cancelKeyboard
        )
        await botStages.UserAdvancedScreenplay.advanced_photo_upload.set()
        user_shared_data[message.from_user.id] = {"photos": []}


async def additional_promo(message: types.Message, state: FSMContext):
    promo = message.text.strip()
    if re.match(PROMO_PATTERN, promo):
        pool = await message.bot.get('pg_pool')
        result = await db.check_user_promo(pool, promo)
        if result:
            async with state.proxy() as data:
                data['promo'] = promo
            await additional_lucky_ticket(message, state)
        else:
            await message.answer(
                f'К сожалению, мы не нашли ваш промокод, либо он не соответствует времени действия промокода😭\n'
                f'Попробуйте ещё раз или нажмите "Отмена"',
                reply_markup=kb.cancelKeyboard
            )
    else:
        await message.answer(
            f'Кажется, вы ввели что-то не то 🤔\n'
            f'Попробуйте ещё раз - одно слово без пробелов',
            reply_markup=kb.cancelKeyboard
        )


async def processing_document_when_uploading_photo(message: types.Message):
    await message.reply(
        f'Пожалуйста, отправьте сжатое фото (поставьте или не убирайте галочку при загрузке на '
        f'"Сжать изображение") 😶',
        reply_markup=kb.cancelKeyboard
    )


async def additional_photo(message: types.Message, state: FSMContext):
    """
    Обработчик фотографий: вызывает добавление фото через очередь задач.
    """
    logging.info(f"Получено сообщение: {message}")

    # Проверяем наличие фото
    if not message.photo:
        await message.answer("⚠ Пожалуйста, отправьте фотографию.")
        return

    file_id = message.photo[-1].file_id

    async with state_lock:  # Блокируем доступ к добавлению фото
        await add_photo_to_queue(file_id, message, state)


async def add_photo_to_queue(file_id: str, message: types.Message, state: FSMContext):
    """
    Добавляет фото в очередь, проверяет лимит и выполняет финализацию.
    """
    user_id = message.from_user.id
    if len(user_shared_data[user_id]['photos']) >= MAX_PHOTOS:
        logging.warning(f"Лимит фото достигнут. Игнорируем фото: {file_id}")
        return

    logging.info(f"Добавляем фото: {file_id}")
    photo_url = await save_photo_to_storage(file_id, message)
    user_shared_data[user_id]['photos'].append(photo_url)

    current_state = await state.get_state()
    if (len(user_shared_data[user_id]['photos']) == MAX_PHOTOS) and (
            current_state == botStages.UserAdvancedScreenplay.advanced_photo_upload.state):
        await finalize_photos(message, state)


async def save_photo_to_storage(file_id: str, message: types.Message) -> str:
    """
    Сохраняет фото в хранилище и возвращает ссылку.
    """
    random_string = ''.join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=10))
    filename = f"{random_string}_photo.jpg"
    photo_url = await s3.save_photo_to_minio(message.bot, file_id, filename, message.from_user.id)
    logging.info(f"Фото сохранено на сервере: {photo_url}")
    return photo_url


async def finalize_photos(message: types.Message, state: FSMContext):
    """
    Завершает обработку после сохранения двух фото.
    """
    logging.info(f"Финализированные фото: {user_shared_data[message.from_user.id]['photos']}")
    await additional_lucky_ticket(message, state)


async def additional_lucky_ticket(message: types.Message, state: FSMContext):
    pool = await message.bot.get('pg_pool')
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    async with state.proxy() as data:
        data['lucky_ticket'] = random_string
    if data.get('promo'):
        await db.additional_with_promo(pool, state, message.from_user.id)
    else:
        await db.additional_with_photos(pool, state, user_shared_data.get(message.from_user.id, {}), message.from_user.id)
    await state.finish()
    await message.answer(
        f'Начинаю проверку, секундочку...'
    )
    await message.answer(
        f'Поздравляю, ваш отзыв зарегистрирован!\n'
        f'Номер вашего счастливого купона: {random_string}'
    )
    await advanced_stage(message)


async def advanced_stage(message: types.Message):
    await botStages.UserAdvancedScreenplay.advanced.set()
    await message.bot.send_photo(
        message.chat.id,
        photo=InputFile('photos/marketplaces.jpg'),
        caption=(
            f'Больше покупок - больше шанс выиграть главный приз! Получи дополнительный купон за новую покупку:\n'
            f'1. Покупайте средства YARKOST\n'
            f'2. Регистрируйте покупку и получайте за каждую счастливый купон'),
        reply_markup=kb.marketsInline,
    )
    await message.answer(
        f'Зайдите в личный Кабинет или зарегестрируйте покупку!',
        reply_markup=kb.lkKeyboard
    )


async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        f'Понял вас! Возвращаемся к основному меню',
        reply_markup=ReplyKeyboardRemove()
    )
    await botStages.UserAdvancedScreenplay.advanced.set()
    await advanced_stage(message)


def register_advanced_handlers(dp: Dispatcher):
    dp.register_message_handler(cancel_handler,
                                state=botStages.UserAdvancedScreenplay.states,
                                content_types=types.ContentType.TEXT, text=['Отмена'])
    dp.register_message_handler(personal_account, state=botStages.UserAdvancedScreenplay.advanced,
                                content_types=types.ContentType.TEXT,
                                text=['Личный кабинет'])
    dp.register_message_handler(additional_play, state=botStages.UserAdvancedScreenplay.advanced,
                                content_types=types.ContentType.TEXT,
                                text=['Дополнительный купон'])
    dp.register_message_handler(additional_product, state=botStages.UserAdvancedScreenplay.advanced_product,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(additional_purchase_location,
                                state=botStages.UserAdvancedScreenplay.advanced_purchase_location,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(additional_promo, state=botStages.UserAdvancedScreenplay.advanced_promo,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(processing_document_when_uploading_photo,
                                state=botStages.UserAdvancedScreenplay.advanced_photo_upload,
                                content_types=types.ContentType.DOCUMENT)
    dp.register_message_handler(additional_photo, state=botStages.UserAdvancedScreenplay.advanced_photo_upload,
                                content_types=types.ContentType.PHOTO)
    dp.register_message_handler(advanced_stage, state=botStages.UserAdvancedScreenplay.advanced)
