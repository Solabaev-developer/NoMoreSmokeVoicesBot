from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# Объявляем локальный router
router = Router()

@router.message(F.text == "/start")
async def cmd_start(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Начать")]],
        resize_keyboard=True
    )
    await msg.answer(
        "Добро пожаловать в NoMoreSmokeVoicesBot!\n"
        "Нажмите «Начать», чтобы перейти в меню.",
        reply_markup=kb
    )

@router.message(F.text == "Начать")
async def on_start(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Добавить стикер")],
            [KeyboardButton(text="Добавить теги к последнему стикеру")],
            [KeyboardButton(text="Поиск по тегам"), KeyboardButton(text="Удалить стикер")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await msg.answer("Выберите действие:", reply_markup=kb)