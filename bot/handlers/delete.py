from aiogram import Router, types
from aiogram.filters import Command

from database.db import find_anime
from keyboards.inline import delete_keyboard

router = Router()

@router.message(Command("delete"))
async def delete(message: types.Message):
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        await message.answer("❌ Использование:\n/delete Название аниме")
        return

    query = args[1].strip()

    if not query:
        await message.answer("❌ Использование:\n/delete Название аниме")
        return

    matches = find_anime(message.from_user.id, query)

    if not matches:
        await message.answer("❌ Ничего не найдено в твоём списке.")
        return

    if len(matches) == 1:
        record_id, title = matches[0]
        await message.answer(
            f"Удалить «{title}»?",
            reply_markup=delete_keyboard(matches)
        )
    else:
        await message.answer(
            "🔍 Найдено несколько совпадений, выбери нужное:",
            reply_markup=delete_keyboard(matches)
        )