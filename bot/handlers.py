import asyncpg
import uuid
from aiogram import Router, F
from aiogram.types import Message, InlineQuery, InlineQueryResultCachedVoice, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

router = Router()
db: asyncpg.Connection = None  # <- здесь будет храниться соединение

# 1) Определяем состояния
class NewVoice(StatesGroup):
    waiting_for_voice = State()
    waiting_for_name = State()
    waiting_for_tags  = State()

@router.message(F.text == "/newvoice")
async def cmd_newvoice(msg: Message, state: FSMContext):
    await state.clear()
    await state.set_state(NewVoice.waiting_for_voice)
    await msg.answer("📝 Отправьте голосовое для нового стикера-войса.")

@router.message(NewVoice.waiting_for_voice, F.voice)
async def process_voice(msg: Message, state: FSMContext):
    await state.update_data(file_id=msg.voice.file_id)
    await msg.answer("✅ Голос принят. Теперь введите имя стикера.")
    await state.set_state(NewVoice.waiting_for_name)

@router.message(NewVoice.waiting_for_name)
async def process_name(msg: Message, state: FSMContext):
    name = msg.text.strip()
    if not name:
        return await msg.answer("❗️Имя не может быть пустым. Пожалуйста, введите текстовое имя.")
    await state.update_data(name=name)
    await msg.answer("🆔 Имя сохранено. Введите, пожалуйста, теги через запятую (например: `привет,тест`).")
    await state.set_state(NewVoice.waiting_for_tags)

@router.message(NewVoice.waiting_for_tags)
async def process_tags(msg: Message, state: FSMContext):
    raw = msg.text.strip()
    tags = [t.strip().lower() for t in raw.split(",") if t.strip()]
    if not tags:
        return await msg.answer("❗️Теги не распознаны. Укажите через запятую хотя бы один тег.")
    data = await state.get_data()
    file_id = data["file_id"]
    name    = data["name"]
    user_id = msg.from_user.id

    # пишем в БД
    await db.execute(
        """
        INSERT INTO voices (user_id, file_id, name, tags)
        VALUES ($1, $2, $3, $4)
        """,
        user_id, file_id, name, tags
    )

    await msg.answer(f"🎉 Добавлено: «{name}» с тегами {', '.join(tags)}")
    await state.clear()  # завершаем диалог, сбрасываем состояние

@router.message(F.voice)
async def handle_voice(msg: Message, state: FSMContext):
    conn = db
    file_id = msg.voice.file_id
    user_id = msg.from_user.id

    await conn.execute(
        "INSERT INTO voices (user_id, file_id, tags) VALUES ($1, $2, $3)",
        user_id, file_id, []
    )
    await msg.answer("Голосовое получено. Отправь теги через /tag теги")

@router.message(F.text.startswith('/tag'))
async def handle_tag(msg: Message):
    conn = db
    tags = msg.text.replace('/tag', '').strip().split(',')
    tags = [t.strip().lower() for t in tags]

    await conn.execute(
        """
        UPDATE voices
        SET tags = $1
        WHERE id = (
            SELECT id
            FROM voices
            WHERE user_id = $2
            ORDER BY created_at DESC
            LIMIT 1
            )
        """,
        tags, msg.from_user.id
    )
    await msg.answer("Теги сохранены.")

@router.message(F.text.startswith('/search'))
async def handle_search(msg: Message):
    conn = db
    keyword = msg.text.replace('/search', '').strip().lower()

    row = await conn.fetchrow(
        "SELECT file_id FROM voices WHERE $1 = ANY(tags) ORDER BY created_at DESC LIMIT 1",
        keyword
    )
    if row:
        await msg.answer_voice(row['file_id'])
    else:
        await msg.answer("Ничего не найдено.")


@router.inline_query()
async def handle_inline(query: InlineQuery):
    text = query.query.strip().lower()

    if text:
        # Поиск по тегам
        rows = await db.fetch(
            """
            SELECT id, file_id, name
            FROM voices
            WHERE $1 = ANY(tags)
            ORDER BY created_at DESC
                LIMIT 10
            """,
            text
        )
    else:
        # Последние 10 загруженных, если нет текста
        rows = await db.fetch(
            """
            SELECT id, file_id, name
            FROM voices
            ORDER BY created_at DESC
                LIMIT 10
            """
        )

    results = []
    for row in rows:
        title = row["name"] or f"Голос #{row['id']}"
        results.append(
            InlineQueryResultCachedVoice(
                id=str(uuid.uuid4()),
                voice_file_id=row["file_id"],
                title=title
            )
        )

    await query.answer(
        results=results,
        cache_time=30,
        is_personal=True
    )

@router.message(F.text.startswith('/name'))
async def handle_name(msg: Message):
    conn = db
    # вытаскиваем всё после "/name"
    name = msg.text.replace('/name', '').strip()
    if not name:
        await msg.answer("Пожалуйста, укажите имя: `/name моё имя`")
        return

    # обновляем последнюю запись пользователя
    await conn.execute(
        """
        UPDATE voices
        SET name = $1
        WHERE id = (
            SELECT id
            FROM voices
            WHERE user_id = $2
            ORDER BY created_at DESC
            LIMIT 1
            )
        """,
        name, msg.from_user.id
    )
    await msg.answer(f"Имя сохранено: «{name}»")