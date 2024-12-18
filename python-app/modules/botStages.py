from aiogram.dispatcher.filters.state import State, StatesGroup


class UserRegistrationScreenplay(StatesGroup):
    fio = State()
    contact = State()
    email = State()
    birthday = State()
    product = State()
    purchase_location = State()
    promo = State()
    photo_upload = State()


class UserAdvancedScreenplay(StatesGroup):
    advanced = State()
    advanced_product = State()
    advanced_photo = State()


class AdminScreenPlay(StatesGroup):
    admin_start = State()
    admin_promo = State()
    admin_promo_add = State()
    admin_promo_change = State()
