from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from database.db import add_anime, delete_anime_by_id, update_watched_episode, set_yummy_url
from database.db import set_watch_reminder_interval, set_episode_check_interval
from keyboards.inline import voice_keyboard, watch_reminder_keyboard, episode_check_keyboard, link_choice_keyboard
from services.anilist import current_known_episode, status_label
from services.shikimori import get_russian_title
from bot.states import VoiceInput, ProgressInput, LinkInput, TitleInput
from keyboards.inline import (
    voice_keyboard, watch_reminder_keyboard, episode_check_keyboard,
    link_choice_keyboard, title_choice_keyboard
)

router = Router()

search_cache: dict[int, dict] = {}
pending_voice: dict[int, int] = {}
pending_add: dict[int, dict] = {}     # user_id -> {"anilist_id", "voice", "watched_episode"}
pending_progress: dict[int, dict] = {}  # user_id -> {"record_id"}
pending_link: dict[int, dict] = {}    # user_id -> {"mode": "new"/"update", ...}
pending_title: dict[int, dict] = {}  # user_id -> {"anilist_id", "voice", "watched_episode"}


def _fallback_title(anime: dict) -> str:
    return anime["title"]["romaji"] or anime["title"]["english"] or anime["title"]["native"]


async def _resolve_title(anime: dict):
    fallback = _fallback_title(anime)
    russian = await get_russian_title(fallback)
    return (russian, fallback)


async def _save_anime(user_id: int, anilist_id: int, voice: str, watched_episode: int,
                       title: str, yummy_url: str = ""):
    anime = search_cache.get(anilist_id)
    if not anime:
        return None, "❌ Данные устарели, выполните /add заново"

    current_episode = current_known_episode(anime)
    status = anime.get("status", "")
    total_episodes = anime.get("episodes")

    added = add_anime(
        user_id, anilist_id, title, voice,
        watched_episode=watched_episode,
        total_episodes=total_episodes,
        status=status,
        current_aired_episode=current_episode,
        yummy_url=yummy_url
    )

    if not added:
        return None, f"⚠️ «{title}» уже есть в твоём списке."

    lines = [f"✅ «{title}» добавлено в список!", f"Статус: {status_label(status)}"]
    if total_episodes:
        lines.append(f"Всего серий в сезоне: {total_episodes}")
        remaining_air = max(total_episodes - current_episode, 0)
        if remaining_air:
            lines.append(f"Ещё не вышло: {remaining_air} сер.")
    if yummy_url:
        lines.append(f"🔗 {yummy_url}")

    return title, "\n".join(lines)


@router.callback_query(lambda c: c.data and c.data.startswith("anime:"))
async def process_anime_selection(callback: types.CallbackQuery):
    anilist_id = int(callback.data.split(":")[1])

    if anilist_id not in search_cache:
        await callback.answer("❌ Данные устарели, выполните /add заново", show_alert=True)
        return

    await callback.message.edit_text(
        "🎙 Выбери озвучку (по желанию):",
        reply_markup=voice_keyboard(anilist_id)
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("voice_skip:"))
async def process_voice_skip(callback: types.CallbackQuery, state: FSMContext):
    anilist_id = int(callback.data.split(":")[1])
    pending_add[callback.from_user.id] = {"anilist_id": anilist_id, "voice": ""}
    await state.set_state(ProgressInput.waiting_for_episode)
    await callback.message.edit_text("📺 На какой серии остановился? Напиши число (0, если ещё не смотрел).")
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("voice_custom:"))
async def process_voice_custom(callback: types.CallbackQuery, state: FSMContext):
    anilist_id = int(callback.data.split(":")[1])
    pending_voice[callback.from_user.id] = anilist_id
    await state.set_state(VoiceInput.waiting_for_voice)
    await callback.message.edit_text("✏️ Напиши название озвучки текстом:")
    await callback.answer()


@router.message(VoiceInput.waiting_for_voice)
async def process_voice_text(message: types.Message, state: FSMContext):
    anilist_id = pending_voice.pop(message.from_user.id, None)
    if anilist_id is None:
        await state.clear()
        await message.answer("❌ Что-то пошло не так, начни заново через /add")
        return

    voice = message.text.strip()[:50]
    pending_add[message.from_user.id] = {"anilist_id": anilist_id, "voice": voice}
    await state.set_state(ProgressInput.waiting_for_episode)
    await message.answer("📺 На какой серии остановился? Напиши число (0, если ещё не смотрел).")


@router.callback_query(lambda c: c.data and c.data.startswith("voice:"))
async def process_voice_popular(callback: types.CallbackQuery, state: FSMContext):
    _, anilist_id, voice = callback.data.split(":", 2)
    pending_add[callback.from_user.id] = {"anilist_id": int(anilist_id), "voice": voice}
    await state.set_state(ProgressInput.waiting_for_episode)
    await callback.message.edit_text("📺 На какой серии остановился? Напиши число (0, если ещё не смотрел).")
    await callback.answer()


@router.message(ProgressInput.waiting_for_episode)
async def process_progress_input(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    raw = message.text.strip()
    watched_episode = int(raw) if raw.isdigit() else 0
    await state.clear()

    progress_pending = pending_progress.pop(user_id, None)
    if progress_pending is not None:
        updated = update_watched_episode(progress_pending["record_id"], user_id, watched_episode)
        if updated:
            await message.answer(f"✅ Прогресс обновлён: серия {watched_episode}")
        else:
            await message.answer("❌ Не удалось обновить прогресс.")
        return

    add_pending = pending_add.pop(user_id, None)
    if add_pending is None:
        await message.answer("❌ Что-то пошло не так, начни заново")
        return

    add_pending["watched_episode"] = watched_episode

    anime = search_cache.get(add_pending["anilist_id"])
    if not anime:
        await message.answer("❌ Данные устарели, выполните /add заново")
        return

    russian, fallback = await _resolve_title(anime)
    suggested_title = russian or fallback

    pending_title[user_id] = add_pending
    pending_title[user_id]["suggested_title"] = suggested_title

    if russian:
        text = f"Название: «{suggested_title}»\nОставить как есть или ввести своё?"
    else:
        text = f"❗ Русского названия не нашлось.\nПредлагаемое название: «{suggested_title}»\nОставить как есть или ввести своё?"

    await message.answer(text, reply_markup=title_choice_keyboard())

@router.callback_query(lambda c: c.data == "link_skip")
async def process_link_skip(callback: types.CallbackQuery):
    pending = pending_link.pop(callback.from_user.id, None)
    if pending is None or pending["mode"] != "new":
        await callback.answer()
        return

    data = pending["data"]
    pending_title.pop(callback.from_user.id, None)
    _, text = await _save_anime(
        callback.from_user.id, data["anilist_id"], data["voice"],
        data["watched_episode"], data["suggested_title"]
    )
    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(lambda c: c.data == "link_add")
async def process_link_add(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in pending_link:
        await callback.answer()
        return
    await state.set_state(LinkInput.waiting_for_link)
    await callback.message.edit_text("✏️ Пришли ссылку на просмотр (например, с yummyanime.tv):")
    await callback.answer()


@router.message(LinkInput.waiting_for_link)
async def process_link_text(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    url = message.text.strip()
    await state.clear()

    pending = pending_link.pop(user_id, None)
    if pending is None:
        await message.answer("❌ Что-то пошло не так, начни заново")
        return

    if pending["mode"] == "new":
        data = pending["data"]
        pending_title.pop(user_id, None)
        _, text = await _save_anime(
            user_id, data["anilist_id"], data["voice"],
            data["watched_episode"], data["suggested_title"], yummy_url=url
        )
        await message.answer(text)
    else:
        record_id = pending["record_id"]
        updated = set_yummy_url(record_id, user_id, url)
        if updated:
            await message.answer(f"✅ Ссылка сохранена:\n{url}")
        else:
            await message.answer("❌ Не удалось сохранить ссылку.")

@router.callback_query(lambda c: c.data and c.data.startswith("delete:"))
async def process_delete_selection(callback: types.CallbackQuery):
    record_id = int(callback.data.split(":")[1])
    deleted = delete_anime_by_id(record_id, callback.from_user.id)

    if deleted:
        await callback.message.edit_text("🗑 Удалено из списка.")
    else:
        await callback.message.edit_text("❌ Не удалось удалить (уже удалено?).")
    await callback.answer()


@router.callback_query(lambda c: c.data == "delete_cancel")
async def process_delete_cancel(callback: types.CallbackQuery):
    await callback.message.edit_text("Отменено.")
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("progress_pick:"))
async def process_progress_pick(callback: types.CallbackQuery, state: FSMContext):
    record_id = int(callback.data.split(":")[1])
    pending_progress[callback.from_user.id] = {"record_id": record_id}
    await state.set_state(ProgressInput.waiting_for_episode)
    await callback.message.edit_text("📺 На какой серии теперь остановился? Напиши число.")
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("link_pick:"))
async def process_link_pick(callback: types.CallbackQuery, state: FSMContext):
    record_id = int(callback.data.split(":")[1])
    pending_link[callback.from_user.id] = {"mode": "update", "record_id": record_id}
    await state.set_state(LinkInput.waiting_for_link)
    await callback.message.edit_text("✏️ Пришли новую ссылку на просмотр:")
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("set_watch_reminder:"))
async def process_set_watch_reminder(callback: types.CallbackQuery):
    hours = int(callback.data.split(":")[1])
    set_watch_reminder_interval(callback.from_user.id, hours)
    text = "🔕 Напоминания о просмотре выключены." if hours == 0 else f"🔔 Буду напоминать каждые {hours} ч."
    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("set_episode_check:"))
async def process_set_episode_check(callback: types.CallbackQuery):
    hours = int(callback.data.split(":")[1])
    set_episode_check_interval(callback.from_user.id, hours)
    await callback.message.edit_text(f"✅ Буду проверять новые серии каждые {hours} ч.")
    await callback.answer()

@router.callback_query(lambda c: c.data == "title_keep")
async def process_title_keep(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    pending = pending_title.get(user_id)
    if pending is None:
        await callback.answer()
        return

    pending_link[user_id] = {"mode": "new", "data": pending}
    await callback.message.edit_text(
        "🔗 Хочешь добавить ссылку на просмотр (например, с yummyanime.tv)?",
        reply_markup=link_choice_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "title_custom")
async def process_title_custom(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in pending_title:
        await callback.answer()
        return
    await state.set_state(TitleInput.waiting_for_title)
    await callback.message.edit_text("✏️ Напиши своё название для этого аниме:")
    await callback.answer()


@router.message(TitleInput.waiting_for_title)
async def process_title_text(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await state.clear()

    pending = pending_title.pop(user_id, None)
    if pending is None:
        await message.answer("❌ Что-то пошло не так, начни заново")
        return

    pending["suggested_title"] = message.text.strip()[:100]
    pending_link[user_id] = {"mode": "new", "data": pending}

    await message.answer(
        "🔗 Хочешь добавить ссылку на просмотр (например, с yummyanime.tv)?",
        reply_markup=link_choice_keyboard()
    )