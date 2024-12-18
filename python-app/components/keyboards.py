from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

# play button
playerInline = InlineKeyboardMarkup(row_width=1)
playerInline.add(InlineKeyboardButton(text='УЧАСТВУЮ', callback_data='play'))

# cancel button
cancelInline = InlineKeyboardMarkup(text='Назад')

# share contact keyboard
shareContactKeyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
contactButtonInline = InlineKeyboardButton('Поделиться контактом', request_contact=True)
shareContactKeyboard.add(contactButtonInline)

# select product keyboard
productKeyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
productKeyboard.add('Сыворотка').add('Шампунь').add('Спрей-гидролат').add('Мыло').add('Масло-суфле')

# choice purchase location
purchaseLocationKeyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
purchaseLocationKeyboard.add('Маркет').add('Маркетплейс')

# advertising buttons
marketsInline = InlineKeyboardMarkup(row_width=3)
marketsInline.add(
    InlineKeyboardButton(text='ЗОЛОТОЕ ЯБЛОКО', url='https://goldapple.ru/brands/yarkost?ysclid=m2ye2yhv3i794709439')
).add(
    InlineKeyboardButton(text='WB', url='https://www.wildberries.ru/brands/yarkost-1032169')
).add(
    InlineKeyboardButton(text='OZON', url='https://www.ozon.ru/brand/yarcost-organic-100426903/')
)

# advanced keyboard
lkKeyboard = ReplyKeyboardMarkup(resize_keyboard=True)
lkKeyboard.add('Личный кабинет').add('Дополнительный купон')

# admin keyboard
mainKeyboardAdmin = ReplyKeyboardMarkup(resize_keyboard=True)
mainKeyboardAdmin.add('Выгрузить базу данных пользователей').add('Выгрузить по промокоду').add('Промокоды')

# admin promo keyboard
promoKeyboardAdmin = ReplyKeyboardMarkup(resize_keyboard=True)
promoKeyboardAdmin.add('Вывести список промокодов').add('Добавить промокод').add('Изменить промокод').add(cancelInline)

# cancel keyboard
cancelKeyboard = ReplyKeyboardMarkup(resize_keyboard=True)
cancelKeyboard.add(cancelInline)
