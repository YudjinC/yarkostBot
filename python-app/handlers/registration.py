import asyncio

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InputFile, ReplyKeyboardRemove

from components import database as db
from components import keyboards as kb
from components import utils
from components import s3
from modules import botStages
from handlers.advanced import advanced_stage
import logging
import random
import string
import re

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
PROMO_PATTERN = r'^[a-zA-Zа-яА-Я0-9]+$'

MAX_PHOTOS = 2
shared_data = {"photos": []}
state_lock = asyncio.Lock()


async def play(callback_query: types.CallbackQuery):
    if callback_query.data == 'play':
        await botStages.UserRegistrationScreenplay.fio.set()
        await callback_query.bot.send_message(
            chat_id=callback_query.from_user.id,
            text=f'Как я могу к вам обращаться?\n\n'
                 f'Напишите мне сюда сообщением⬇',
            reply_markup=kb.cancelKeyboard
        )


async def add_nickname(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['fio'] = message.text
    await message.answer(
        f'Куда звонить, когда вы окажетесь победителем главного приза?\n'
        f'Нажмите на кнопку под клавиатурой',
        reply_markup=kb.shareContactKeyboard
    )
    await botStages.UserRegistrationScreenplay.next()


async def add_contact(message: types.Message, state: FSMContext):
    contact = message.contact
    async with state.proxy() as data:
        data['contact'] = contact.phone_number
    await message.answer(
        f'Если не дозвонимся, на какой адрес email писать поздравления с победой в розыгрыше?',
        reply_markup=kb.cancelKeyboard
    )
    await botStages.UserRegistrationScreenplay.next()


async def contact_not_shared(message: types.Message):
    await message.answer(
        f'Пожалуйста, нажмите кнопку "Поделиться контактом"😔',
        reply_markup=kb.shareContactKeyboard
    )


async def add_email(message: types.Message, state: FSMContext):
    email = message.text.strip()
    if re.match(EMAIL_REGEX, email):
        async with state.proxy() as data:
            data['email'] = email
        await message.answer(
            f'Когда ваш день рождения? Хотим тепло вас поздравить и отправить подарок!💖',
            reply_markup=kb.cancelKeyboard
        )
        await botStages.UserRegistrationScreenplay.next()
    else:
        await message.answer(
            f'Это не похоже на email🤔\n'
            f'Пожалуйста, попробуйте ещё раз, у вас получится!!!'
        )


async def add_birthday(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['birthday'] = message.text
    await message.answer(
        f'Супер!\n'
        f'Теперь выберите купленный товар и нажмите на кнопку!',
        reply_markup=kb.productKeyboard
    )
    await botStages.UserRegistrationScreenplay.next()


async def add_product(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['product'] = message.text
    await message.answer(
        f'Покупали на маркетплейсе или на маркет?',
        reply_markup=kb.purchaseLocationKeyboard
    )
    await botStages.UserRegistrationScreenplay.next()


async def add_purchase_location(message: types.Message, state: FSMContext):
    purchase_location = message.text
    async with state.proxy() as data:
        data['purchase_location'] = purchase_location
    if purchase_location == 'Маркет':
        await message.answer(
            f'Введите, пожалуйста, промокод 💗\n'
            f'Это должно быть одно слово без пробелов!!',
            reply_markup=kb.cancelKeyboard
        )
        await botStages.UserRegistrationScreenplay.promo.set()
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
        await botStages.UserRegistrationScreenplay.photo_upload.set()


async def add_promo(message: types.Message, state: FSMContext):
    promo = message.text.strip()
    if re.match(PROMO_PATTERN, promo):
        pool = await message.bot.get('pg_pool')
        result = await db.check_user_promo(pool, promo)
        if result:
            async with state.proxy() as data:
                data['promo'] = promo
            await add_lucky_ticket(message, state)
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


async def add_photos(message: types.Message, state: FSMContext):
    """
    Обработчик фотографий: вызывает добавление фото через очередь задач.
    """
    logging.info(f"Получено сообщение: {message}")

    # Проверяем наличие фото
    if not message.photo:
        await message.answer(
            f'⚠ Пожалуйста, отправьте фотографию.',
            reply_markup=kb.cancelKeyboard
        )
        return

    file_id = message.photo[-1].file_id

    async with state_lock:  # Блокируем доступ к добавлению фото
        await add_photo_to_queue(file_id, message, state)


async def add_photo_to_queue(file_id: str, message: types.Message, state: FSMContext):
    """
    Добавляет фото в очередь, проверяет лимит и выполняет финализацию.
    """
    # Проверяем лимит
    if len(shared_data['photos']) >= MAX_PHOTOS:
        logging.warning(f"Лимит фото достигнут. Игнорируем фото: {file_id}")
        return

    # Добавляем фото и сохраняем
    logging.info(f"Добавляем фото: {file_id}")
    photo_url = await save_photo_to_storage(file_id, message)
    shared_data['photos'].append(photo_url)

    if len(shared_data['photos']) == 1:
        await message.answer("✅ Поздравляю, первая фотография сохранена!")
    elif len(shared_data['photos']) == MAX_PHOTOS:
        await message.answer("✅ Поздравляю, ваша вторая фотография сохранена!")
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
    await message.answer("🎉 Спасибо! Обе фотографии загружены и сохранены.")
    logging.info(f"Финализированные фото: {shared_data['photos']}")
    await add_lucky_ticket(message, state)


async def add_lucky_ticket(message: types.Message, state: FSMContext):
    pool = await message.bot.get('pg_pool')
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    async with state.proxy() as data:
        data['lucky_ticket'] = random_string
    if data.get('promo'):
        await db.registration_with_promo(pool, state, message.from_user.id)
    else:
        await db.registration_with_photos(pool, state, shared_data, message.from_user.id)
    await state.finish()
    await message.answer(
        f'Начинаю проверку, секундочку...'
    )
    await message.answer(
        f'Поздравляю, ваш отзыв зарегистрирован!\n'
        f'Номер вашего счастливого купона: {random_string}'
    )
    await botStages.UserAdvancedScreenplay.advanced.set()
    await advanced_stage(message)


async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        f'Понял вас! Сбрасываю регистрацию',
        reply_markup=ReplyKeyboardRemove()
    )
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


def register_registration_handlers(dp: Dispatcher):
    dp.register_message_handler(cancel_handler,
                                state=botStages.UserRegistrationScreenplay.states,
                                content_types=types.ContentType.TEXT, text=['Отмена'])
    dp.register_callback_query_handler(play, lambda c: c.data == 'play')
    dp.register_message_handler(add_nickname, state=botStages.UserRegistrationScreenplay.fio,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(add_contact, state=botStages.UserRegistrationScreenplay.contact,
                                content_types=types.ContentType.CONTACT)
    dp.register_message_handler(contact_not_shared, state=botStages.UserRegistrationScreenplay.contact)
    dp.register_message_handler(add_email, state=botStages.UserRegistrationScreenplay.email,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(add_birthday, state=botStages.UserRegistrationScreenplay.birthday,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(add_product, state=botStages.UserRegistrationScreenplay.product,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(add_purchase_location, state=botStages.UserRegistrationScreenplay.purchase_location,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(add_promo, state=botStages.UserRegistrationScreenplay.promo,
                                content_types=types.ContentType.TEXT)
    dp.register_message_handler(processing_document_when_uploading_photo,
                                state=botStages.UserRegistrationScreenplay.photo_upload,
                                content_types=types.ContentType.DOCUMENT)
    dp.register_message_handler(add_photos, state=botStages.UserRegistrationScreenplay.photo_upload,
                                content_types=types.ContentType.PHOTO)
