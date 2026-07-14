from aiogram import Router, types
from aiogram.filters import Command

from database.db import get_anime_full
from services.anilist import status_label

router = Router()

@router.message(Command("list"))
async def list_anime(message: types.Message):
    data = get_anime_full(message.from_user.id)

    if not data:
        await message.answer("📭 Список пуст")
        return

    lines = []
    for record_id, title, watched, voice, total_episodes, status, last_notified, yummy_url in data:
        voice_part = f" [{voice}]" if voice else ""
        line = f"• {title}{voice_part} — {status_label(status)}"

        if total_episodes:
            line += f"\n  Просмотрено: {watched}/{total_episodes}"
            remaining_to_watch = max((last_notified or 0) - watched, 0)
            remaining_to_air = max(total_episodes - (last_notified or 0), 0)
            if remaining_to_watch:
                line += f" (осталось посмотреть: {remaining_to_watch})"
            if remaining_to_air:
                line += f"\n  Осталось выйти: {remaining_to_air} сер."
        else:
            line += f"\n  Просмотрено: {watched} сер."

        if yummy_url:
            line += f"\n  🔗 {yummy_url}"

        lines.append(line)

    text = "\n\n".join(lines)
    await message.answer(f"📺 Твой список:\n\n{text}")