from aiogram import types, Dispatcher


async def fallback_message_handler(message: types.Message):
    """
    Обработчик сообщений, которые не попадают в другие обработчики.
    """
    await message.reply('Извините, не понимаю вас 😨\n'
                        'Попробуйте ещё раз, нажмите кнопку действия, '
                        'используйте "назад" или "отмена"!')


def register_fallback_handlers(dp: Dispatcher):
    dp.register_message_handler(fallback_message_handler, state="*", content_types=types.ContentType.ANY)
