from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InputFile

from components import database as db
from components import keyboards as kb
from modules import botStages

import random
import string


async def personal_account(message: types.Message):
    pool = await message.bot.get('pg_pool')
    personal_account_data = await db.personal_account(pool, message.from_user.id)
    await message.answer(
        f'{personal_account_data[0]}, это ваш личный кабинет!\n\n'
        f'Номера ваших счастливых билетиков:\n'
        f'{personal_account_data[1]}\n'
        f'Следи за результатами в группе @yarkostorganic !'
    )


async def additional_play(message: types.Message,  state: FSMContext):
    await message.bot.send_photo(
        message.chat.id,
        photo=InputFile('photos/marketplaces.jpg'),
        caption=f'💖 Оставьте честный отзыв о спрей-гидролат от YARKOST\n'
                f'📎Прикрепите здесь 2 скрина:\n'
                f'чек об оплате с маркетплейса и отзыв с артикулом товара, воспользовавшись скрепкой около клавиатуры.',
    )
    await botStages.Screenplay.advanced_photo.set()
    await additional_photo(message, state)


async def dont_added_photo(message: types.Message):
    await message.answer(
        f'Вы не отправили фотографии...😑'
    )


async def additional_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['photo'] = message.photo[0].file_id
    await botStages.Screenplay.next()
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
    await botStages.Screenplay.advanced.set()
    await advanced_stage(message)


async def advanced_stage(message: types.Message):
    await botStages.Screenplay.advanced.set()
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
    dp.register_message_handler(personal_account, state=botStages.Screenplay.advanced, text=['Личный кабинет'])
    dp.register_message_handler(additional_play, state=botStages.Screenplay.advanced, text=['Дополнительный купон'])
    dp.register_message_handler(dont_added_photo, state=botStages.Screenplay.advanced_photo)
    dp.register_message_handler(additional_photo, state=botStages.Screenplay.advanced_photo, content_types=['photo'])
    dp.register_message_handler(additional_lucky_ticket, state=botStages.Screenplay.advanced_lucky_ticket)
    dp.register_message_handler(advanced_stage, state=botStages.Screenplay.advanced)
