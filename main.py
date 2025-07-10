# main.py
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, InputMediaPhoto, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
import logging
import sqlite3
import os

API_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# === Database setup ===
conn = sqlite3.connect("bot.db")
cursor = conn.cursor()
cursor.execute(
    "CREATE TABLE IF NOT EXISTS users ("
    "tg_id INTEGER PRIMARY KEY, "
    "name TEXT, "
    "age INTEGER, "
    "gender TEXT, "
    "interests TEXT, "
    "bio TEXT, "
    "photo TEXT, "
    "is_premium INTEGER DEFAULT 0, "
    "lang TEXT DEFAULT 'en')"
)
conn.commit()

# === Language dictionary ===
LANG = {
    'en': {
        'start': "👋 Welcome! Let's create your profile. What's your name?",
        'ask_age': "Nice! How old are you?",
        'ask_gender': "What is your gender? (e.g. Male, Female, Other)",
        'ask_interests': "List a few interests (comma separated):",
        'ask_bio': "Write a short bio about yourself:",
        'ask_photo': "📷 Please send a photo for your profile:",
        'profile_saved': "✅ Your profile has been created! Soon you'll be able to browse others.",
        'invalid_age': "Please enter a number.",
        'lang_choice': "Choose your language / 选择语言 / Выберите язык"
    },
    'ru': {
        'start': "👋 Добро пожаловать! Давай создадим твою анкету. Как тебя зовут?",
        'ask_age': "Отлично! Сколько тебе лет?",
        'ask_gender': "Какой у тебя пол? (например: Мужской, Женский, Другое)",
        'ask_interests': "Напиши несколько интересов через запятую:",
        'ask_bio': "Кратко расскажи о себе:",
        'ask_photo': "📷 Пришли фото для анкеты:",
        'profile_saved': "✅ Твоя анкета сохранена! Скоро ты сможешь смотреть других.",
        'invalid_age': "Пожалуйста, введи число.",
        'lang_choice': "Выбери язык / Choose language / 选择语言"
    },
    'zh': {
        'start': "👋 欢迎！让我们创建你的资料。你叫什么名字？",
        'ask_age': "很好！你几岁？",
        'ask_gender': "你的性别是？（例如：男，女，其他）",
        'ask_interests': "列出一些兴趣（用逗号分隔）：",
        'ask_bio': "简单介绍一下你自己：",
        'ask_photo': "📷 请发送一张照片作为你的头像：",
        'profile_saved': "✅ 你的资料已创建！很快你将可以浏览他人。",
        'invalid_age': "请输入一个数字。",
        'lang_choice': "选择语言 / Choose language / Выберите язык"
    }
}

# === FSM states ===
class Registration(StatesGroup):
    lang = State()
    name = State()
    age = State()
    gender = State()
    interests = State()
    bio = State()
    photo = State()

# === Handlers ===
@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="English", callback_data="lang_en")],
        [InlineKeyboardButton(text="Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="中文", callback_data="lang_zh")]
    ])
    await message.answer(LANG['en']['lang_choice'], reply_markup=kb)
    await state.set_state(Registration.lang)

@dp.callback_query(Registration.lang)
async def choose_lang(callback: CallbackQuery, state: FSMContext):
    lang_code = callback.data.split('_')[1]
    await state.update_data(lang=lang_code)
    await callback.message.answer(LANG[lang_code]['start'])
    await state.set_state(Registration.name)

@dp.message(Registration.name)
async def reg_name(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data['lang']
    await state.update_data(name=message.text)
    await message.answer(LANG[lang]['ask_age'])
    await state.set_state(Registration.age)

@dp.message(Registration.age)
async def reg_age(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data['lang']
    if not message.text.isdigit():
        return await message.answer(LANG[lang]['invalid_age'])
    await state.update_data(age=int(message.text))
    await message.answer(LANG[lang]['ask_gender'])
    await state.set_state(Registration.gender)

@dp.message(Registration.gender)
async def reg_gender(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data['lang']
    await state.update_data(gender=message.text)
    await message.answer(LANG[lang]['ask_interests'])
    await state.set_state(Registration.interests)

@dp.message(Registration.interests)
async def reg_interests(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data['lang']
    await state.update_data(interests=message.text)
    await message.answer(LANG[lang]['ask_bio'])
    await state.set_state(Registration.bio)

@dp.message(Registration.bio)
async def reg_bio(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data['lang']
    await state.update_data(bio=message.text)
    await message.answer(LANG[lang]['ask_photo'])
    await state.set_state(Registration.photo)

@dp.message(Registration.photo, F.photo)
async def reg_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    lang = data['lang']
    cursor.execute("REPLACE INTO users (tg_id, name, age, gender, interests, bio, photo, lang) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (message.from_user.id, data['name'], data['age'], data['gender'], data['interests'], data['bio'], photo_id, lang))
    conn.commit()
    await message.answer(LANG[lang]['profile_saved'])
    await state.clear()

# === Start polling ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
