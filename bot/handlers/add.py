from aiogram import Router, types
from aiogram.filters import Command

from services.anilist import search_anime
from keyboards.inline import anime_keyboard
from bot.handlers.callback import search_cache

router = Router()

@router.message(Command("add"))
async def add(message: types.Message):
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        await message.answer("❌ Использование:\n/add Название аниме")
        return

    query = args[1]
    results = await search_anime(query)

    if not results:
        await message.answer("❌ Ничего не найдено.")
        return

    for anime in results:
        search_cache[anime["id"]] = anime

    await message.answer(
        "🔍 Выберите нужное аниме:",
        reply_markup=anime_keyboard(results)
    )