import asyncio
from aiogram import Bot

from database.db import (
    get_all_tracked_for_check, update_episode_check,
    get_users_due_for_watch_reminder, update_watch_reminder_sent,
    get_unwatched_for_user,
)
from services.anilist import get_anime_details

TICK_SECONDS = 30 * 60  # проверяем расписание каждые 30 минут,
                        # но реально шлём согласно личным настройкам пользователя


async def check_new_episodes_tick():
    due = get_all_tracked_for_check()

    for record_id, user_id, anilist_id, title, last_notified in due:
        try:
            details = await get_anime_details(anilist_id)
        except Exception:
            continue

        next_airing = details.get("nextAiringEpisode")
        total_episodes = details.get("episodes")
        status = details.get("status", "")

        if next_airing:
            latest_episode = next_airing["episode"] - 1
        elif total_episodes:
            latest_episode = total_episodes
        else:
            latest_episode = None

        if latest_episode is None:
            continue

        yield_notify = latest_episode > (last_notified or 0)
        update_episode_check(record_id, latest_episode, status, total_episodes)

        if yield_notify:
            yield (user_id, title, latest_episode)


async def watch_reminder_tick():
    user_ids = get_users_due_for_watch_reminder()

    for user_id in user_ids:
        unwatched = get_unwatched_for_user(user_id)
        update_watch_reminder_sent(user_id)

        if not unwatched:
            continue

        lines = [f"• {title}: серия {watched + 1} из {latest}" for title, watched, latest in unwatched]
        text = "👀 Не забудь досмотреть:\n" + "\n".join(lines)
        yield (user_id, text)


async def run_notifier(bot: Bot):
    while True:
        try:
            async for user_id, title, episode in check_new_episodes_tick():
                try:
                    await bot.send_message(user_id, f"🎬 Вышла новая серия!\n«{title}» — серия {episode}")
                except Exception:
                    pass

            async for user_id, text in watch_reminder_tick():
                try:
                    await bot.send_message(user_id, text)
                except Exception:
                    pass

        except Exception as e:
            print(f"Ошибка в фоновой проверке: {e}")

        await asyncio.sleep(TICK_SECONDS)