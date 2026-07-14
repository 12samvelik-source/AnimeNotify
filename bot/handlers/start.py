from aiogram import Router, types
from aiogram.filters import Command

router = Router()


@router.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 AnimeNotify готов к работе!\n\n"
        "Команды:\n"
        "/add <название> — добавить аниме в список\n"
        "/list — показать твой список\n"
        "/delete <название> — удалить аниме из списка\n"
        "/progress <название> — обновить серию, на которой остановился\n"
        "/link <название> — добавить/изменить ссылку на просмотр\n"
        "/remind_watch — настроить напоминания о просмотре\n"
        "/remind_episodes — настроить частоту проверки новых серий"
    )