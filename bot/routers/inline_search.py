import uuid
from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultCachedVoice
from db import get_db

router = Router()

@router.inline_query()
async def handle_inline(query: InlineQuery):
    text = query.query.strip().lower()

    if text:
        rows = await get_db().fetch(
            """
            SELECT id, file_id, name, speaker
            FROM voices
            WHERE $1 = ANY(tags)
            ORDER BY created_at DESC
                LIMIT 10
            """,
            text
        )
    else:
        rows = await get_db().fetch(
            """
            SELECT id, file_id, name, speaker
            FROM voices
            ORDER BY created_at DESC
                LIMIT 10
            """
        )

    results = [
        InlineQueryResultCachedVoice(
            id=str(uuid.uuid4()),
            voice_file_id=row["file_id"],
            title=f"{row['id']} - {row['name'] or 'Без имени'} - {row.get('speaker') or 'Неизвестно'}"
        )
        for row in rows
    ]

    await query.answer(
        results=results,
        cache_time=30,
        is_personal=True,
        switch_pm_text="Перейти в бота",
        switch_pm_parameter="start"
    )