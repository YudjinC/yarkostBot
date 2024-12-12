from aiogram.dispatcher.filters.state import State, StatesGroup


class Screenplay(StatesGroup):
    fio = State()
    contact = State()
    email = State()
    birthday = State()
    product = State()
    photo = State()
    lucky_ticket = State()
    advanced = State()
    advanced_photo = State()
    advanced_lucky_ticket = State()
