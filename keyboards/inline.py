from aiogram.utils.keyboard import InlineKeyboardBuilder

POPULAR_VOICES = ["AniLibria", "AniDUB", "Ancord", "Jam Club"]

WATCH_REMINDER_OPTIONS = [
    ("Выключить", 0),
    ("Каждые 12 часов", 12),
    ("Раз в сутки", 24),
    ("Раз в 3 дня", 72),
    ("Раз в неделю", 168),
]

EPISODE_CHECK_OPTIONS = [
    ("Каждый час", 1),
    ("Каждые 6 часов", 6),
    ("Раз в сутки", 24),
]


def anime_keyboard(results):
    builder = InlineKeyboardBuilder()
    for anime in results:
        title = anime["title"]["romaji"] or anime["title"]["english"] or anime["title"]["native"]
        builder.button(text=title, callback_data=f"anime:{anime['id']}")
    builder.adjust(1)
    return builder.as_markup()


def voice_keyboard(anilist_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Добавить озвучку", callback_data=f"voice_custom:{anilist_id}")
    builder.button(text="⏭ Без озвучки", callback_data=f"voice_skip:{anilist_id}")
    builder.adjust(1)
    return builder.as_markup()


def delete_keyboard(items):
    builder = InlineKeyboardBuilder()
    for record_id, title in items:
        builder.button(text=title, callback_data=f"delete:{record_id}")
    builder.button(text="Отмена", callback_data="delete_cancel")
    builder.adjust(1)
    return builder.as_markup()


def progress_pick_keyboard(items):
    builder = InlineKeyboardBuilder()
    for record_id, title in items:
        builder.button(text=title, callback_data=f"progress_pick:{record_id}")
    builder.adjust(1)
    return builder.as_markup()


def watch_reminder_keyboard():
    builder = InlineKeyboardBuilder()
    for label, hours in WATCH_REMINDER_OPTIONS:
        builder.button(text=label, callback_data=f"set_watch_reminder:{hours}")
    builder.adjust(1)
    return builder.as_markup()


def episode_check_keyboard():
    builder = InlineKeyboardBuilder()
    for label, hours in EPISODE_CHECK_OPTIONS:
        builder.button(text=label, callback_data=f"set_episode_check:{hours}")
    builder.adjust(1)
    return builder.as_markup()

def link_choice_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Добавить ссылку", callback_data="link_add")
    builder.button(text="⏭ Без ссылки", callback_data="link_skip")
    builder.adjust(1)
    return builder.as_markup()


def link_pick_keyboard(items):
    builder = InlineKeyboardBuilder()
    for record_id, title in items:
        builder.button(text=title, callback_data=f"link_pick:{record_id}")
    builder.adjust(1)
    return builder.as_markup()

def title_choice_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Оставить как есть", callback_data="title_keep")
    builder.button(text="✏️ Своё название", callback_data="title_custom")
    builder.adjust(1)
    return builder.as_markup()