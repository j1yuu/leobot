# Данный скрипт был создан для форума Pawno-Info.Ru пользователем Oleg Polikhronidi
# Пожалуйста, при размещении темы на других порталах - указывайте ссылку на оригинальную тему.
# Единая ссылка позволяет прийти к общим решениям проблем с кодом, спасибо - если указываете ссылку.
# Скрипт опубликован пользователем Oleg Polikhronidi на портале Pawno Info
# Мой профиль на портале: https://pawno-info.ru/members/oleg-polikhronidi.89444/

import random
import logging
from db import BotDB
from aiogram.dispatcher import FSMContext
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

# не знаю как ещё можно было круто назвать переменную
# но анкета - это представление человека (переменная)
bot = Bot(token="6452236490:AAGHn5jiIMXFY1_IHNrKRd8inkeZ-Uk9FS8") # сюда - токен бота
dp = Dispatcher(bot, storage=MemoryStorage()) # определяем ответы
logging.basicConfig(level=logging.INFO) # регистрируем события во время исполнения кода
BotDB = BotDB('database.db') # указываем базу данных

# заготовленные ответы
main_text = '1. Смотреть анкеты\n2. Моя анкета\n3. Удалить анкету'
profile_text = '1. Заполнить анкету заново\n2. Изменить текст анкеты\n3. Изменить фото\n4. Вернутся назад'

def show_profile(name, age, city, text):
    return f'{name}\n{age}\n{city}\n{text}'

def get_random_anketa(list_of_anketi):
    anketa = list_of_anketi[random.randint(0, len(list_of_anketi) - 1)]
    a = anketa
    return [show_profile(a[2], a[3], a[4], a[5]), BotDB.get_photo_id(a[1])]
        
# машина состояний для навигации.
class Wait(StatesGroup):
    choosing_gender = State()
    choosing_interest = State()
    name = State()
    age = State()
    city = State()
    text = State()
    photo = State()
    menu_answer = State()
    my_anketa_answer = State()
    change_text = State()
    change_photo = State()
    delete_confirm = State()
    anketa_reaction = State()

# в случае если анкета есть - показываем анкету
# в случае если анкеты нет - предлагаем создать
@dp.message_handler(commands="start", state = "*")
async def anketa_start(message: types.Message):
    if(not BotDB.user_exists(message.from_user.id)):
        BotDB.add_user(message.from_user.id)

    if(BotDB.anketa_exists(message.from_user.id)):

        anketa = BotDB.get_anketa(message.from_user.id)
        a = anketa[0]
        caption = show_profile(a[2], a[3], a[4], a[5])
        await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), chat_id = message.from_user.id, caption = caption)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["1", "2", "3"]
        keyboard.add(*buttons)

        await message.answer(main_text, reply_markup = keyboard)
        await Wait.menu_answer.set()

    else:

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Парень", "Девушка"]
        keyboard.add(*buttons)

        await message.answer("Заполним анкету!\nДля начала выберите свой пол",
         reply_markup=keyboard)
        await Wait.choosing_gender.set()

@dp.message_handler(state = Wait.choosing_gender)
async def choose_gender(message: types.Message, state: FSMContext):
    if message.text not in ["Парень", "Девушка"]:
        await message.answer("Выберите вариант из кнопок ниже")
        return
    await state.update_data(gender = message.text.lower())

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Парни", "Девушки"]
    keyboard.add(*buttons)
    await message.answer("Кто тебя интересует?", reply_markup = keyboard)
    await Wait.choosing_interest.set()

@dp.message_handler(state = Wait.choosing_interest)
async def choose_interest(message: types.Message, state: FSMContext):
    if message.text == "Парни" or message.text == "Девушки":
        await state.update_data(interest = message.text.lower())
        await message.answer("Введите своё имя", reply_markup=types.ReplyKeyboardRemove())
        await Wait.name.set()
    else:
        await message.answer("Выберите вариант из кнопок ниже")
        return

@dp.message_handler(state = Wait.name)
async def name(message: types.Message, state: FSMContext):
    if len(message.text) > 30:
        await message.answer("Слишком длинное имя")
        return
    await state.update_data(name = message.text)                    
    await message.answer("Сколько вам лет?")
    await Wait.age.set()

@dp.message_handler(state = Wait.age)
async def age(message: types.Message, state: FSMContext):
    try:
        if 10 > int(message.text) or int(message.text) > 100:
            await message.answer("Какой-то странный возраст")
            return
    except(TypeError, ValueError):
        await message.answer("Какой-то странный возраст")
        return
    await state.update_data(age = message.text)
    await message.answer("Напишите свой город")
    await Wait.city.set()

@dp.message_handler(state = Wait.city)
async def city(message: types.Message, state: FSMContext):
    if len(message.text) > 30:
        await message.answer("Слишком длинный город")
        return

    await state.update_data(city = message.text)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Оставить пустым")

    await message.answer("Введите описание анкеты до 200 символов. Можно пропустить.", reply_markup = keyboard)
    await Wait.text.set()

@dp.message_handler(state = Wait.text)
async def text(message: types.Message, state: FSMContext):
    if message.text == "Оставить пустым":
        await state.update_data(text = '')
    else:
        if len(message.text) > 200:
            await message.answer("Описание должно быть длинной до 200 символов")
            return
        await state.update_data(text = message.text)
    
    await message.answer("Загрузите своё фото", reply_markup=types.ReplyKeyboardRemove())
    await Wait.photo.set()

@dp.message_handler(state = Wait.photo, content_types = ["photo"])
async def download_photo(message: types.Message, state: FSMContext):
    await message.photo[-1].download(destination_file=f"photos/{message.from_user.id}.jpg")
# преобразовываем значение словаря в (d)
    data = await state.get_data()
    d = list(data.values())
    print(d)

    BotDB.add_anketa(message.from_user.id, d[0], d[1], d[2], d[3], d[4], d[5])
    caption = show_profile(d[2], d[3], d[4], d[5])
    await message.answer("Так выглядит твоя анкета: ")
    await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["1", "2", "3"]
    keyboard.add(*buttons)

    await message.answer(main_text, reply_markup = keyboard)
    await Wait.menu_answer.set()

@dp.message_handler(state = Wait.menu_answer)
async def menu_answer(message: types.Message, state: FSMContext):
    if message.text == "1":
        anketa = BotDB.get_anketa(message.from_user.id)
        a = anketa[0]
        caption = show_profile(a[2], a[3], a[4], a[5])       

        list_of_anketi = BotDB.find_anketi(message.from_user.id, a[7], a[4], a[3])

        try:
            get_random_anketa(list_of_anketi)
        except ValueError:
            await message.answer("Никого не могу найти. Возможно, твой город некорректный / не популярный.")

            await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)
            
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = ["1", "2", "3", "4"]
            keyboard.add(*buttons)

            await message.answer(profile_text, reply_markup = keyboard)
            await Wait.my_anketa_answer.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Лайк", "Скип", "Вернутся назад"]
        keyboard.add(*buttons)
        anketa = get_random_anketa(list_of_anketi)
        caption = anketa[0]
        photo_id = anketa[1]

        await state.update_data(liked_id = photo_id)
        await bot.send_photo(photo = open(f"photos/{photo_id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id, reply_markup = keyboard)
        await Wait.anketa_reaction.set()
        
    elif message.text == "2":

        anketa = BotDB.get_anketa(message.from_user.id)
        a = anketa[0]
        caption = show_profile(a[2], a[3], a[4], a[5])
        await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["1", "2", "3", "4"]
        keyboard.add(*buttons)
        await message.answer(profile_text, reply_markup = keyboard)
        await Wait.my_anketa_answer.set()

    elif message.text == "3":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Да", "Нет"]
        keyboard.add(*buttons)
        await message.answer("Вы точно хотите удалить свою анкету?", reply_markup = keyboard)
        await Wait.delete_confirm.set()

    else:
        await message.answer("Выберите вариант из кнопок ниже")
        return

@dp.message_handler(state = Wait.anketa_reaction)
async def anketa_reaction(message: types.Message, state: FSMContext):
    if message.text == "Лайк":
        
        data = await state.get_data()
        d = list(data.values())

        anketa = BotDB.get_anketa(message.from_user.id)
        a = anketa[0]
        caption = show_profile(a[2], a[3], a[4], a[5])

        list_of_anketi = BotDB.find_anketi(message.from_user.id, data["interest"], data["city"], data["age"])

        liked_id = data["liked_id"]

        await bot.send_message(text = "Вы понравились этому человеку: ", chat_id = liked_id)
        await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), chat_id = liked_id, caption = caption)
        await bot.send_message(text = f"Начинай общатся, если понравлися(лась) - @{message.from_user.username}", chat_id = liked_id)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Лайк", "Скип", "Вернутся назад"]
        keyboard.add(*buttons)

        anketa = get_random_anketa(list_of_anketi)
        caption = anketa[0]
        photo_id = anketa[1]
        
        await bot.send_photo(photo = open(f"photos/{photo_id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)
        await Wait.anketa_reaction.set()

    elif message.text == "Скип":

        data = await state.get_data()
        list_of_anketi = BotDB.find_anketi(message.from_user.id, data["interest"], data["city"], data["age"])

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Лайк", "Скип", "Вернутся назад"]
        keyboard.add(*buttons)

        caption = get_random_anketa(list_of_anketi)[0]
        photo_id = get_random_anketa(list_of_anketi)[1]
        await bot.send_photo(photo = open(f"photos/{photo_id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)

        await Wait.anketa_reaction.set()

    elif message.text == "Вернутся назад":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["1", "2", "3"]
        keyboard.add(*buttons)

        await message.answer(main_text, reply_markup = keyboard)
        await Wait.menu_answer.set()
    else:
        await message.answer("Выберите вариант из кнопок")
        return

@dp.message_handler(state = Wait.delete_confirm)
async def delete_confirm(message: types.Message, state: FSMContext):
    if message.text == "Да":
        BotDB.delete_anketa(message.from_user.id)
        BotDB.delete_user(message.from_user.id)
        await message.answer("Ваша анкета удалена!\nВы можете вернутся сюда в любое время по команде /start", reply_markup = types.ReplyKeyboardRemove())        
    elif message.text == "Нет":
        anketa = BotDB.get_anketa(message.from_user.id)
        a = anketa[0]
        caption = show_profile(a[2], a[3], a[4], a[5])

        await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)
        
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["1", "2", "3", "4"]
        keyboard.add(*buttons)

        await message.answer(profile_text, reply_markup = keyboard)
        await Wait.my_anketa_answer.set()
    else:
        await message.answer("Выберите вариант из кнопок ниже")
        return

@dp.message_handler(state = Wait.my_anketa_answer)
async def my_anketa_answer(message: types.Message, state: FSMContext):
# пересоздаем анкету
    if message.text == "1":
        BotDB.delete_anketa(message.from_user.id)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Парень", "Девушка"]
        keyboard.add(*buttons)

        await message.answer("Для начала выберите свой пол",
         reply_markup=keyboard)
        await Wait.choosing_gender.set()
# вводим новый текст
    elif message.text == "2":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Оставить пустым")
        await message.answer("Введите новый текст анкеты", reply_markup=keyboard)
        await Wait.change_text.set()

    elif message.text == "3":
        await message.answer("Загрузите новое фото", reply_markup = types.ReplyKeyboardRemove())
        await Wait.change_photo.set()

    elif message.text == "4":
        anketa = BotDB.get_anketa(message.from_user.id)
        a = anketa[0]
        caption = show_profile(a[2], a[3], a[4], a[5])

        await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["1", "2", "3"]
        keyboard.add(*buttons)

        await message.answer(main_text, reply_markup = keyboard)
        await Wait.menu_answer.set()
    else:
        await message.answer("Выберите вариант из кнопок ниже")
        return

@dp.message_handler(state = Wait.change_text)
async def change_text(message: types.Message, state: FSMContext):
    if message.text == "Оставить пустым":
            BotDB.update_text(message.from_user.id, '')

            anketa = BotDB.get_anketa(message.from_user.id)
            a = anketa[0]
            caption = show_profile(a[2], a[3], a[4], a[5])   

            await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)
            
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = ["1", "2", "3", "4"]
            keyboard.add(*buttons)

            await message.answer(profile_text, reply_markup = keyboard)
            await Wait.my_anketa_answer.set()
    else:
        if len(message.text) > 200:
            await message.answer("Описание должно быть длинной до 200 символов")
            return
        BotDB.update_text(message.from_user.id, message.text)

        anketa = BotDB.get_anketa(message.from_user.id)
        a = anketa[0]
        caption = show_profile(a[2], a[3], a[4], a[5])   

        await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["1", "2", "3"]
        keyboard.add(*buttons)

        await message.answer(main_text, reply_markup = keyboard)
        await Wait.menu_answer.set()

@dp.message_handler(state = Wait.change_photo, content_types = ["photo"])
async def change_photo(message: types.Message, state: FSMContext):
    await message.photo[-1].download(destination_file=f"photos/{message.from_user.id}.jpg")

    anketa = BotDB.get_anketa(message.from_user.id)
    a = anketa[0]
    caption = show_profile(a[2], a[3], a[4], a[5])   

    await message.answer("Вот ваша анкета: ")
    await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["1", "2", "3"]
    keyboard.add(*buttons)

    await message.answer(main_text, reply_markup = keyboard)
    await Wait.menu_answer.set()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
    
# Данный скрипт был создан для форума Pawno-Info.Ru пользователем Oleg Polikhronidi
# Пожалуйста, при размещении темы на других порталах - указывайте ссылку на оригинальную тему.
# Единая ссылка позволяет прийти к общим решениям проблем с кодом, спасибо - если указываете ссылку.
# Скрипт опубликован пользователем Oleg Polikhronidi на портале Pawno Info
# Мой профиль на портале: https://pawno-info.ru/members/oleg-polikhronidi.89444/