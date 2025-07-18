from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from db import get_db

router = Router()

class DeleteStickerStates(StatesGroup):
    waiting_for_sticker_id = State()

@router.message(F.text == "Удалить стикер")
async def prompt_for_sticker_id(msg: Message, state: FSMContext):
    await msg.answer("Введите ID стикера, который нужно удалить:")
    await state.set_state(DeleteStickerStates.waiting_for_sticker_id)

@router.message(DeleteStickerStates.waiting_for_sticker_id)
async def delete_sticker_by_id(msg: Message, state: FSMContext):
    try:
        sticker_id = int(msg.text.strip())
    except ValueError:
        await msg.answer("Некорректный ID. Введите числовой ID.")
        return

    db = get_db()
    result = await db.execute("DELETE FROM voices WHERE id = $1", sticker_id)

    if result == "DELETE 1":
        await msg.answer(f"Стикер с ID {sticker_id} удалён.")
    else:
        await msg.answer(f"Стикер с ID {sticker_id} не найден.")

    await state.clear()