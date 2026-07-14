from aiogram import Router, types
from aiogram.filters import Command

from keyboards.inline import watch_reminder_keyboard, episode_check_keyboard

router = Router()

@router.message(Command("remind_watch"))
async def remind_watch(message: types.Message):
    await message.answer(
        "🔔 Как часто напоминать тебе о просмотре?",
        reply_markup=watch_reminder_keyboard()
    )

@router.message(Command("remind_episodes"))
async def remind_episodes(message: types.Message):
    await message.answer(
        "🔎 Как часто проверять выход новых серий?",
        reply_markup=episode_check_keyboard()
    )