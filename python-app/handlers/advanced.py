from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InputFile
from aiogram.types import ReplyKeyboardRemove

from components import database as db
from components import keyboards as kb
from components import s3
from modules import botStages

import random
import string


async def personal_account(message: types.Message):
    pool = await message.bot.get('pg_pool')
    personal_account_data = await db.personal_account(pool, message.from_user.id)
    await message.answer(
        f'{personal_account_data["fio"]}, это ваш личный кабинет!\n\n'
        f'Номера ваших счастливых билетиков:\n'
        f'{personal_account_data["tickets"]}\n'
        f'Следи за результатами в группе @yarkostorganic !'
    )


async def additional_play(message: types.Message,  state: FSMContext):
    await message.answer(
        f'Выберите купленный товар и нажмите на кнопку!',
        reply_markup=kb.productKeyboard
    )
    await botStages.UserScreenplay.advanced_product.set()


async def additional_product(message: types.Message,  state: FSMContext):
    async with state.proxy() as data:
        data['product'] = message.text
    await message.bot.send_photo(
        message.chat.id,
        photo=InputFile('photos/marketplaces.jpg'),
        caption=f'💖 Оставьте честный отзыв о спрей-гидролат от YARKOST\n'
                f'📎Прикрепите здесь 2 скрина:\n'
                f'чек об оплате с маркетплейса и отзыв с артикулом товара, воспользовавшись скрепкой около клавиатуры.',
        reply_markup=ReplyKeyboardRemove()
    )
    await botStages.UserScreenplay.next()
    await additional_photo(message, state)


async def dont_added_photo(message: types.Message):
    await message.answer(
        f'Вы не отправили фотографии...😑'
    )


async def additional_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        file_id = message.photo[-1].file_id
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        filename = f"user_{message.from_user.id}_{random_string}_photo.jpg"

        photo_url = await s3.save_photo_to_minio(message.bot, file_id, filename)

        data['photo'] = photo_url
    await botStages.UserScreenplay.next()
    await additional_lucky_ticket(message, state)


async def additional_lucky_ticket(message: types.Message, state: FSMContext):
    pool = await message.bot.get('pg_pool')
    await message.answer(
        f'Начинаю проверку, секундочку...'
    )
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    await message.answer(
        f'Поздравляю, ваш отзыв зарегистрирован!\n'
        f'Номер вашего счастливого купона: {random_string}'
    )
    async with state.proxy() as data:
        data['lucky_ticket'] = random_string
    await db.additional_item(pool, state, message.from_user.id)
    await botStages.UserScreenplay.advanced.set()
    await advanced_stage(message)


async def advanced_stage(message: types.Message):
    await botStages.UserScreenplay.advanced.set()
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


def register_advanced_handlers(dp: Dispatcher):
    dp.register_message_handler(personal_account, state=botStages.UserScreenplay.advanced, text=['Личный кабинет'])
    dp.register_message_handler(additional_play, state=botStages.UserScreenplay.advanced, text=['Дополнительный купон'])
    dp.register_message_handler(additional_product, state=botStages.UserScreenplay.advanced_product)
    dp.register_message_handler(dont_added_photo, state=botStages.UserScreenplay.advanced_photo)
    dp.register_message_handler(additional_photo, state=botStages.UserScreenplay.advanced_photo, content_types=['photo'])
    dp.register_message_handler(additional_lucky_ticket, state=botStages.UserScreenplay.advanced_lucky_ticket)
    dp.register_message_handler(advanced_stage, state=botStages.UserScreenplay.advanced)
