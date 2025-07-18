from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from db import get_db
from .keyboards import main_menu

router = Router()


class NewSticker(StatesGroup):
    waiting_for_voice = State()
    waiting_for_name = State()
    waiting_for_speaker = State()
    waiting_for_tags = State()


@router.message(F.text.in_(["/newvoice", "Добавить стикер"]))
async def cmd_newsticker(msg: Message, state: FSMContext):
    await state.clear()
    await state.set_state(NewSticker.waiting_for_voice)
    await msg.answer("📝 Шаг 1/4: отправьте голосовое сообщение для нового стикера.")


@router.message(NewSticker.waiting_for_voice, F.voice)
async def process_newsticker_voice(msg: Message, state: FSMContext):
    row = await get_db().fetchrow(
        "INSERT INTO voices(user_id, file_id, tags) VALUES ($1, $2, $3) RETURNING id",
        msg.from_user.id, msg.voice.file_id, []
    )
    sid = row["id"]
    await state.update_data(sticker_id=sid)
    await msg.answer(
        f"✅ Шаг 1/4 завершён. ID вашего стикера: {sid}\n"
        "📝 Шаг 2/4: введите *имя* для этого стикера.",
        parse_mode="Markdown"
    )
    await state.set_state(NewSticker.waiting_for_name)


@router.message(NewSticker.waiting_for_name)
async def process_newsticker_name(msg: Message, state: FSMContext):
    name = msg.text.strip()
    if not name:
        return await msg.answer("❗️Имя не может быть пустым. Введите текстовое имя.")
    data = await state.get_data()
    sid = data["sticker_id"]
    await get_db().execute(
        "UPDATE voices SET name = $1 WHERE id = $2",
        name, sid
    )
    await state.update_data(name=name)
    await msg.answer(
        f"✅ Шаг 2/4 завершён. Имя сохранено: *{name}*\n"
        "🗣 Шаг 3/4: Кто говорит в этом стикере? (например: Мама, Я, Друг)",
        parse_mode="Markdown"
    )
    await state.set_state(NewSticker.waiting_for_speaker)


@router.message(NewSticker.waiting_for_speaker)
async def process_newsticker_speaker(msg: Message, state: FSMContext):
    speaker = msg.text.strip()
    if not speaker:
        return await msg.answer("❗️Имя говорящего не может быть пустым. Введите ещё раз.")
    data = await state.get_data()
    sid = data["sticker_id"]
    await get_db().execute(
        "UPDATE voices SET speaker = $1 WHERE id = $2",
        speaker, sid
    )
    await state.update_data(speaker=speaker)
    await msg.answer(
        f"✅ Шаг 3/4 завершён. Говорит: *{speaker}*\n"
        "🏷 Шаг 4/4: введите теги через запятую (например: `привет,тест`).",
        parse_mode="Markdown"
    )
    await state.set_state(NewSticker.waiting_for_tags)


@router.message(NewSticker.waiting_for_tags)
async def process_newsticker_tags(msg: Message, state: FSMContext):
    tags = [t.strip().lower() for t in msg.text.split(",") if t.strip()]
    if not tags:
        return await msg.answer("❗️Укажите хотя бы один тег через запятую.")
    data = await state.get_data()
    sid = data["sticker_id"]
    name = data.get("name", "Без имени")
    speaker = data.get("speaker", "Неизвестно")

    await get_db().execute(
        "UPDATE voices SET tags = $1 WHERE id = $2",
        tags, sid
    )

    await msg.answer(
        f"🎉 Стикер *{name}* (ID `{sid}`) успешно сохранён.\n"
        f"🗣 Говорит: {speaker}\n"
        f"🏷 Теги: `{', '.join(tags)}`",
        parse_mode="Markdown",
        reply_markup=main_menu
    )
    await state.clear()