from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database.db import find_anime
from keyboards.inline import progress_pick_keyboard
from bot.states import ProgressInput
from bot.handlers.callback import pending_progress

router = Router()

@router.message(Command("progress"))
async def progress(message: types.Message, state: FSMContext):
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        await message.answer("❌ Использование:\n/progress Название аниме")
        return

    matches = find_anime(message.from_user.id, args[1].strip())

    if not matches:
        await message.answer("❌ Ничего не найдено в твоём списке.")
        return

    if len(matches) == 1:
        record_id, title = matches[0]
        pending_progress[message.from_user.id] = {"record_id": record_id}
        await state.set_state(ProgressInput.waiting_for_episode)
        await message.answer(f"📺 «{title}»: на какой серии остановился? Напиши число.")
    else:
        await message.answer(
            "🔍 Найдено несколько совпадений, выбери нужное:",
            reply_markup=progress_pick_keyboard(matches)
        )