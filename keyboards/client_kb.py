from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
b1 = KeyboardButton('Подобрать подпись')
b4 = KeyboardButton('Заказать подбор подписей у каллиграфа')
kb_client = ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
kb_client.add(b1).add(b4)

b2 = KeyboardButton('Пропустить')
kb_client_skip_middle = ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
kb_client_skip_middle.add(b2)

b3 = KeyboardButton('Создать анимацию')
kb_client_gif = ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
kb_client_gif.add(b1).add(b3)