# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Добавить стикер")],
        [KeyboardButton(text="Добавить теги к последнему стикеру")],
        [KeyboardButton(text="Поиск по тегам"), KeyboardButton(text="Удалить стикер")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)