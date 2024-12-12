from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

playerInline = InlineKeyboardMarkup(row_width=1)
playerInline.add(InlineKeyboardButton(text='УЧАСТВУЮ', callback_data='play'))

marketsInline = InlineKeyboardMarkup(row_width=3)
marketsInline.add(
    InlineKeyboardButton(text='ЗОЛОТОЕ ЯБЛОКО', url='https://goldapple.ru/brands/yarkost?ysclid=m2ye2yhv3i794709439')
).add(
    InlineKeyboardButton(text='WB', url='https://www.wildberries.ru/brands/yarkost-1032169')
).add(
    InlineKeyboardButton(text='OZON', url='https://www.ozon.ru/brand/yarcost-organic-100426903/')
)

productKeyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
productKeyboard.add('Сыворотка').add('Шампунь').add('Спрей-гидролат').add('Мыло').add('Масло-суфле')

shareContactKeyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
contactButton = InlineKeyboardButton("Поделиться контактом", request_contact=True)
shareContactKeyboard.add(contactButton)

lkKeyboard = ReplyKeyboardMarkup(resize_keyboard=True)
lkKeyboard.add('Личный кабинет').add('Дополнительный купон')
