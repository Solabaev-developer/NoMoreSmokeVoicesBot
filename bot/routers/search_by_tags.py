from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from db import get_db

router = Router()

class SearchState(StatesGroup):
    waiting_for_tag = State()

@router.message(F.text == "Поиск по тегам")
async def start_tag_search(msg: Message, state: FSMContext):
    await state.set_state(SearchState.waiting_for_tag)
    await msg.answer("Введите тег для поиска (без запятой):")

@router.message(SearchState.waiting_for_tag)
async def perform_tag_search(msg: Message, state: FSMContext):
    tag = msg.text.strip().lower()
    if not tag:
        return await msg.answer("❗️Введите непустой тег.")

    rows = await get_db().fetch(
        "SELECT id, name FROM voices WHERE $1 = ANY(tags)",
        tag
    )

    if not rows:
        await msg.answer(f"Ничего не найдено по тегу: `{tag}`", parse_mode="Markdown")
    else:
        result = "\n".join(
            f"🔹 *{r['name']}* (ID `{r['id']}`)" if r['name'] else f"ID `{r['id']}`"
            for r in rows
        )
        await msg.answer(
            f"Найдено {len(rows)} стикеров по тегу `{tag}`:\n\n{result}",
            parse_mode="Markdown"
        )

    await state.clear()