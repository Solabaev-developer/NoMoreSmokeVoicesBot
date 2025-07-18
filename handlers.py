import asyncpg
import uuid
from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineQuery,
    InlineQueryResultCachedVoice,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ContentType,
    ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

router = Router()
db: asyncpg.Connection = None  # заполняется в main.py

# —————————————————————————————
#  Главное меню: /start → «Начать» → команды
# —————————————————————————————

@router.message(F.text == "/start")
async def cmd_start(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Начать")]],
        resize_keyboard=True
    )
    await msg.answer(
        "Добро пожаловать в NoMoreSmokeVoicesBot!\nНажмите «Начать», чтобы перейти в меню.",
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


# —————————————————————————————
#  FSM для добавления нового стикера: voice → name → tags
# —————————————————————————————

class NewSticker(StatesGroup):
    waiting_for_voice = State()
    waiting_for_name  = State()   # <--- добавлено
    waiting_for_tags  = State()

@router.message(F.text.in_(["/newvoice", "Добавить стикер"]))
async def cmd_newsticker(msg: Message, state: FSMContext):
    await state.clear()
    await state.set_state(NewSticker.waiting_for_voice)
    await msg.answer("📝 Шаг 1/3: отправьте голосовое сообщение для нового стикера.")

@router.message(NewSticker.waiting_for_voice, F.voice)
async def process_newsticker_voice(msg: Message, state: FSMContext):
    row = await db.fetchrow(
        "INSERT INTO voices(user_id, file_id, tags) VALUES ($1, $2, $3) RETURNING id",
        msg.from_user.id, msg.voice.file_id, []
    )
    sid = row["id"]
    await state.update_data(sticker_id=sid)
    await msg.answer(
        f"✅ Шаг 1/3 завершён. ID вашего стикера: {sid}\n"
        "📝 Шаг 2/3: введите *имя* для этого стикера.",
        parse_mode="Markdown"
    )
    await state.set_state(NewSticker.waiting_for_name)

@router.message(NewSticker.waiting_for_name)
async def process_newsticker_name(msg: Message, state: FSMContext):
    name = msg.text.strip()
    if not name:
        return await msg.answer("❗️Имя не может быть пустым. Введите текстовое имя.")
    data = await state.get_data()
    sid  = data["sticker_id"]
    await db.execute(
        "UPDATE voices SET name = $1 WHERE id = $2",
        name, sid
    )
    await state.update_data(name=name)
    await msg.answer(
        f"✅ Шаг 2/3 завершён. Имя сохранено: *{name}*\n"
        "📝 Шаг 3/3: введите теги через запятую (например: `привет,тест`).",
        parse_mode="Markdown"
    )
    await state.set_state(NewSticker.waiting_for_tags)

@router.message(NewSticker.waiting_for_tags)
async def process_newsticker_tags(msg: Message, state: FSMContext):
    tags = [t.strip().lower() for t in msg.text.split(",") if t.strip()]
    if not tags:
        return await msg.answer("❗️Укажите хотя бы один тег через запятую.")
    data = await state.get_data()
    sid  = data["sticker_id"]
    name = data["name"]
    await db.execute(
        "UPDATE voices SET tags = $1 WHERE id = $2",
        tags, sid
    )
    await msg.answer(
        f"🎉 Стикер *{name}* (ID `{sid}`) добавлен с тегами: `{', '.join(tags)}`",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()


# —————————————————————————————
#  Inline-поиск с отображением ID и имени
# —————————————————————————————

@router.inline_query()
async def handle_inline(query: InlineQuery):
    text = query.query.strip().lower()
    if text:
        rows = await db.fetch(
            "SELECT id, file_id, name FROM voices WHERE $1 = ANY(tags) ORDER BY created_at DESC LIMIT 10",
            text
        )
    else:
        rows = await db.fetch(
            "SELECT id, file_id, name FROM voices ORDER BY created_at DESC LIMIT 10"
        )

    results = []
    for r in rows:
        title = f"{r['id']} — {r['name'] or 'Без имени'}"
        results.append(
            InlineQueryResultCachedVoice(
                id=str(uuid.uuid4()),
                voice_file_id=r["file_id"],
                title=title
            )
        )

    await query.answer(
        results=results,
        cache_time=30,
        is_personal=True,
        switch_pm_text="Перейти в бота",
        switch_pm_parameter="start"
    )