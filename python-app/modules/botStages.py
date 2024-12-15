from aiogram.dispatcher.filters.state import State, StatesGroup


class UserScreenplay(StatesGroup):
    fio = State()
    contact = State()
    email = State()
    birthday = State()
    product = State()
    photo = State()
    lucky_ticket = State()
    advanced = State()
    advanced_product = State()
    advanced_photo = State()
    advanced_lucky_ticket = State()


class AminScreenPlay(StatesGroup):
    admin_start = State()
