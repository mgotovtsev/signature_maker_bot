import csv, os
import io, re

import aiofiles
from aiogram import types, Dispatcher
from aiogram.types import InputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from get_signature import GetSignature
from create_bot import dp, bot
from keyboards import kb_client, kb_client_skip_middle, kb_client_gif


nMaxEffectCount = 30
nChunkSize      = 10

sStat_DirPath      = 'stat'
sStat_CsvPath      = os.path.join(sStat_DirPath, 'stat.csv')
sOrderStat_CsvPath = os.path.join(sStat_DirPath, 'order_stat.csv')
reNamePattern      = re.compile('[^a-zA-Zа-яА-Я]')

sWelcomeMessage = '''Благодаря использованию специальных алгоритмов и технологий, бот генерирует красивую и элегантную подпись✍, которая может быть использована в качестве электронной подписи на документах или просто в качестве декоративного элемента.\n
Для начала работы с ботом нужно ввести команду "Подобрать подпись" и далее свое имя и фамилию. После этого бот автоматически создаст уникальное изображение подписи, которое можно сохранить💾 или поделиться с кем-то. Любую подпись можно анимировать.\n
Подписывайтесь на группу бота @signature_maker 🙏'
'''

class FsmClient(StatesGroup):
    stateName       = State()
    stateSurname    = State()
    stateMiddleName = State()
    stateGetAnimation_EnterEffectNumber = State()
    stateGetAnimation_PushButton = State()


async def WriteStat(sStat_CsvPath, message, data):
    if not os.path.exists(os.path.dirname(sStat_CsvPath)): os.makedirs(os.path.dirname(sStat_CsvPath))
    if not os.path.exists(sStat_CsvPath):
        async with aiofiles.open(sStat_CsvPath, mode='w', encoding="utf-8") as csvStat:
            await csvStat.write('date,id,is_bot,first_name,last_name,username,language_code,is_premium,added_to_attachment_menu,can_join_groups,can_read_all_group_messages,supports_inline_queries,name,surname,middle_name\n')

    async with aiofiles.open(sStat_CsvPath, mode='a+', encoding="utf-8") as csvStat:
        sStatRow = str(message.date)                                   + ','
        sStatRow += str(message.from_user.id)                          + ','
        sStatRow += str(message.from_user.is_bot)                      + ',"'
        sStatRow += str(message.from_user.first_name)                  + '","'
        sStatRow += str(message.from_user.last_name)                   + '","'
        sStatRow += str(message.from_user.username)                    + '",'
        sStatRow += str(message.from_user.language_code)               + ','
        sStatRow += str(message.from_user.is_premium)                  + ','
        sStatRow += str(message.from_user.added_to_attachment_menu)    + ','
        sStatRow += str(message.from_user.can_join_groups)             + ','
        sStatRow += str(message.from_user.can_read_all_group_messages) + ','
        sStatRow += str(message.from_user.supports_inline_queries)     + ','
        sStatRow += data['name']        + ','
        sStatRow += data['surname']     + ','
        sStatRow += data['middle_name'] + '\n'
        print(sStatRow.strip())
        await csvStat.write(sStatRow)


async def check_name(message, state):
    sName = reNamePattern.sub('', message.text.strip()[:15])
    if not sName:
        await message.answer('Введены недопустимые символы. Начните заново.', reply_markup = kb_client)
        await state.finish()
        return
    return sName.capitalize()


async def get_signature_JPEG(message: types.Message, data):
    sSurname  = data['name']
    sName     = data['surname']
    sMiddle   = data['middle_name']

    for nLowEffectNumberBorder in range(1, nMaxEffectCount + 1, nChunkSize):
        media       = types.MediaGroup()
        listBuffers = list()
        for nEffectId in range(nLowEffectNumberBorder, nLowEffectNumberBorder + nChunkSize):
            if nEffectId not in [21, 22]:
                if not data['middle_name'] and nEffectId == 14:
                    continue
                img = await GetSignature(sSurname, sName, sMiddle, nEffectId = nEffectId)
            else:
                img = await GetSignature(sSurname, sName, sMiddle,
                                        nWidth = 700, nHeight = 350,
                                        nEffectId = nEffectId,
                                        nLineWidth = 3)
            if not img:
                continue
            buffer = io.BytesIO()
            img.save(buffer, format = 'JPEG', quality = 100)
            buffer.seek(0)
            input_file = InputFile(buffer)
            media.attach_photo(input_file, 'Подпись №%s' % nEffectId)
            listBuffers.append(buffer)
        await bot.send_media_group(chat_id = message.chat.id, media = media)
        for buffer in listBuffers:
            buffer.close()


async def get_signature_GIF(message: types.Message, data, nEffectId):
    sSurname   = data['name']
    sName      = data['surname']
    sMiddle    = data['middle_name']

    if nEffectId not in [21, 22]:
        if not data['middle_name'] and nEffectId == 14:
            return False
        img, listImages = await GetSignature(sSurname, sName, sMiddle, nEffectId = nEffectId, sFormat = 'GIF')
    else:
        img, listImages = await GetSignature(sSurname, sName, sMiddle,
                                             nWidth = 700, nHeight = 350,
                                             nEffectId = nEffectId,
                                             nLineWidth = 3, sFormat = 'GIF')

    if not img:
        return False

    buffer = io.BytesIO()
    img.save(buffer, format = 'GIF', save_all = True, append_images = listImages, duration = 150, loop = 1, optimize = False)
    buffer.seek(0)
    input_file = InputFile(buffer, filename = f'Подпись №{nEffectId}.gif')
    await bot.send_animation(message.chat.id, input_file, caption = f'Подпись №{nEffectId}.gif')
    buffer.close()
    return True


async def set_kb_for_animation(data):
    if 'animated_signatures' not in data:
        data['animated_signatures'] = list()
    kb_get_gifs = ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
    for i in range(1, nMaxEffectCount + 1):
        if not data['middle_name'] and i == 14:
            continue
        if i not in data['animated_signatures']:
            kb_get_gifs.insert(KeyboardButton(str(i)))
        else:
            kb_get_gifs.add(KeyboardButton(str(i) + ' (Готово)'))
    kb_get_gifs.add(KeyboardButton('Выход'))
    data['kb_for_animation'] = kb_get_gifs


async def send_welcome(message: types.Message):
    await message.answer(sWelcomeMessage, reply_markup = kb_client)


async def order_signature(message: types.Message):
    await message.answer('Наши партнёры: онлайн-сервис по созданию подписей https://onetwosign.ru')

    if not os.path.exists(os.path.dirname(sOrderStat_CsvPath)): os.makedirs(os.path.dirname(sOrderStat_CsvPath))
    if not os.path.exists(sOrderStat_CsvPath):
        async with aiofiles.open(sOrderStat_CsvPath, mode='w', encoding="utf-8") as csvStat:
            await csvStat.write('date,id,is_bot,first_name,last_name,username,language_code,is_premium,added_to_attachment_menu,can_join_groups,can_read_all_group_messages,supports_inline_queries\n')

    async with aiofiles.open(sOrderStat_CsvPath, mode='a+', encoding="utf-8") as csvStat:
        sStatRow = str(message.date)                                   + ','
        sStatRow += str(message.from_user.id)                          + ','
        sStatRow += str(message.from_user.is_bot)                      + ',"'
        sStatRow += str(message.from_user.first_name)                  + '","'
        sStatRow += str(message.from_user.last_name)                   + '","'
        sStatRow += str(message.from_user.username)                    + '",'
        sStatRow += str(message.from_user.language_code)               + ','
        sStatRow += str(message.from_user.is_premium)                  + ','
        sStatRow += str(message.from_user.added_to_attachment_menu)    + ','
        sStatRow += str(message.from_user.can_join_groups)             + ','
        sStatRow += str(message.from_user.can_read_all_group_messages) + ','
        sStatRow += str(message.from_user.supports_inline_queries)     + '\n'
        print('-=ORDER=-', sStatRow.strip())
        await csvStat.write(sStatRow)


async def cm_start(message: types.Message, state : FSMContext):
    await message.answer('Введите своё имя.', reply_markup = ReplyKeyboardRemove())
    await state.reset_data()
    async with state.proxy() as data:
        data['name']                = ''
        data['surname']             = ''
        data['middle_name']         = ''
        data['animated_signatures'] = list()
    await FsmClient.next()


async def get_name(message: types.Message, state : FSMContext):
    sName = await check_name(message, state)
    if not sName: return
    async with state.proxy() as data:
        data['name'] = sName
    await message.answer('Введите свою фамилию.', reply_markup = ReplyKeyboardRemove())
    await FsmClient.next()


async def get_surname(message: types.Message, state : FSMContext):
    sSurname = await check_name(message, state)
    if not sSurname: return
    async with state.proxy() as data:
        data['surname'] = sSurname
    await message.answer('Введите своё отчество, либо нажмите "Пропустить".', reply_markup = kb_client_skip_middle)
    await FsmClient.next()


async def get_middle_name(message: types.Message, state : FSMContext):
    sMiddle = await check_name(message, state)
    if not sMiddle: return
    async with state.proxy() as data:
        if message.text == 'Пропустить':
            data['middle_name'] = ''
            await message.answer('🕗 Рисую подписи по имени и фамилии... ', reply_markup = ReplyKeyboardRemove())
        else:
            data['middle_name'] = sMiddle
            await message.answer('🕗 Рисую подписи...', reply_markup = ReplyKeyboardRemove())
        await get_signature_JPEG(message, data)
        await message.answer('Создание подписей завершено. Вы можете начать заново, либо создать анимацию подписи.', reply_markup = kb_client_gif)
        await WriteStat(sStat_CsvPath, message, data)
    await FsmClient.next()


async def get_animation_enter_effect_number(message: types.Message, state : FSMContext):
    if message.text == 'Создать анимацию':
        async with state.proxy() as data:
            await set_kb_for_animation(data)
            await message.answer('Выберите номер подписи для создания анимации. Нажмите на картинку с подписью, чтобы узнать её номер.', reply_markup = data['kb_for_animation'])
        await FsmClient.next()
    else:
        await state.finish()
        await message.answer('Создание подписей завершено. Вы можете начать заново.', reply_markup = kb_client)


async def get_animation_push_button(message: types.Message, state : FSMContext):
    if message.text == 'Выход':
        await state.finish()
        await message.answer('Создание подписей завершено. Вы можете начать заново.', reply_markup = kb_client)
    elif message.text.isnumeric() and int(message.text) >= 1 and int(message.text) <= nMaxEffectCount:
        nEffectId = int(message.text)
        await message.answer('🕗 Создание анимации...', reply_markup = ReplyKeyboardRemove())

        async with state.proxy() as data:

            if not('middle_name' in data and 'animated_signatures' in data):
                await state.finish()
                await message.answer('Создание подписей завершено. Вы можете начать заново.', reply_markup = kb_client)
                return

            if data['middle_name'] or nEffectId != 14:
                await get_signature_GIF(message, data, nEffectId)

            if len(data['animated_signatures']) > 1:
                await state.finish()
                await message.answer('Достигнут лимит создания анимаций. Вы можете начать заново.', reply_markup = kb_client)
            else:
                data['animated_signatures'].append(nEffectId)
                await set_kb_for_animation(data)
                await message.answer('Выберите номер подписи для создания анимации.', reply_markup = data['kb_for_animation'])
    else:
        await message.answer('Выберите номер подписи для создания анимации.')


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(send_welcome   , commands = ['start', 'help'])
    dp.register_message_handler(order_signature, lambda message: message.text == "Заказать подбор подписей у каллиграфа")
    dp.register_message_handler(cm_start       , lambda message: message.text == "Подобрать подпись", state = None)
    dp.register_message_handler(get_name       , state = FsmClient.stateName)
    dp.register_message_handler(get_surname    , state = FsmClient.stateSurname)
    dp.register_message_handler(get_middle_name, state = FsmClient.stateMiddleName)
    dp.register_message_handler(get_animation_enter_effect_number, state = FsmClient.stateGetAnimation_EnterEffectNumber)
    dp.register_message_handler(get_animation_push_button, state = FsmClient.stateGetAnimation_PushButton)