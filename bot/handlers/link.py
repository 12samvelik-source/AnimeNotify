from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database.db import find_anime
from keyboards.inline import link_pick_keyboard
from bot.states import LinkInput
from bot.handlers.callback import pending_link

router = Router()

@router.message(Command("link"))
async def link(message: types.Message, state: FSMContext):
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        await message.answer("❌ Использование:\n/link Название аниме")
        return

    matches = find_anime(message.from_user.id, args[1].strip())

    if not matches:
        await message.answer("❌ Ничего не найдено в твоём списке.")
        return

    if len(matches) == 1:
        record_id, title = matches[0]
        pending_link[message.from_user.id] = {"mode": "update", "record_id": record_id}
        await state.set_state(LinkInput.waiting_for_link)
        await message.answer(f"✏️ Пришли ссылку на просмотр для «{title}»:")
    else:
        await message.answer(
            "🔍 Найдено несколько совпадений, выбери нужное:",
            reply_markup=link_pick_keyboard(matches)
        )