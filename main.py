import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from dotenv import load_dotenv

from database.db import init_db
from bot.handlers import router
from services.notifier import run_notifier

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

dp.include_router(router)


async def set_commands():
    commands = [
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="add", description="Добавить аниме в список"),
        BotCommand(command="list", description="Показать список аниме"),
        BotCommand(command="delete", description="Удалить аниме из списка"),
        BotCommand(command="progress", description="Обновить просмотренную серию"),
        BotCommand(command="link", description="Добавить/изменить ссылку на просмотр"),
        BotCommand(command="remind_watch", description="Настроить напоминания о просмотре"),
        BotCommand(command="remind_episodes", description="Настроить проверку новых серий"),
    ]
    await bot.set_my_commands(commands)


async def main():
    init_db()
    print("Bot is starting...")

    await set_commands()
    asyncio.create_task(run_notifier(bot))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())