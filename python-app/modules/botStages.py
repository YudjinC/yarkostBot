from aiogram.dispatcher.filters.state import State, StatesGroup


class UserScreenplay(StatesGroup):
    fio = State()
    contact = State()
    email = State()
    birthday = State()
    product = State()
    photo = State()
    # photo1 = State()
    # photo2 = State()
    lucky_ticket = State()
    advanced = State()
    advanced_product = State()
    advanced_photo = State()
    advanced_lucky_ticket = State()


class AdminScreenPlay(StatesGroup):
    admin_start = State()
    admin_promo = State()
    admin_promo_add = State()
    admin_promo_change = State()
