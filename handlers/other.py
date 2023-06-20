from aiogram import types, Dispatcher
from create_bot import dp


async def all_message(message: types.Message):
    pass


def register_handlers_other(dp: Dispatcher):
    dp.register_message_handler(all_message)