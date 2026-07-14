import sqlite3
from datetime import datetime, timezone

DB_PATH = "database/anime.db"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def hours_since(iso_str: str) -> float:
    if not iso_str:
        return 9999
    then = datetime.fromisoformat(iso_str)
    if then.tzinfo is None:
        then = then.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - then
    return delta.total_seconds() / 3600


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_anime (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        anilist_id INTEGER,
        title TEXT,
        watched_episode INTEGER DEFAULT 0,
        voice TEXT DEFAULT '',
        total_episodes INTEGER,
        status TEXT DEFAULT '',
        last_notified_episode INTEGER DEFAULT 0,
        last_episode_check_at TEXT DEFAULT '',
        yummy_url TEXT DEFAULT ''
    )
    """)

    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_user_anime_unique
    ON user_anime(user_id, anilist_id)
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        episode_check_interval_hours INTEGER DEFAULT 6,
        watch_reminder_interval_hours INTEGER DEFAULT 0,
        last_watch_reminder_at TEXT DEFAULT ''
    )
    """)

    conn.commit()
    conn.close()


def add_anime(user_id, anilist_id, title, voice="", watched_episode=0,
              total_episodes=None, status="", current_aired_episode=0, yummy_url=""):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO user_anime
            (user_id, anilist_id, title, watched_episode, voice,
             total_episodes, status, last_notified_episode, last_episode_check_at, yummy_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, anilist_id, title, watched_episode, voice,
             total_episodes, status, current_aired_episode, now_iso(), yummy_url)
        )
        conn.commit()
        added = True
    except sqlite3.IntegrityError:
        added = False
    finally:
        conn.close()

    return added


def get_anime_full(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, title, watched_episode, voice, total_episodes, status, last_notified_episode, yummy_url
        FROM user_anime
        WHERE user_id = ?
        """,
        (user_id,)
    )

    data = cur.fetchall()
    conn.close()
    return data


def find_anime(user_id: int, query: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    safe_query = query.strip().replace("%", "\\%").replace("_", "\\_")

    cur.execute(
        "SELECT id, title FROM user_anime WHERE user_id = ? AND title LIKE ? ESCAPE '\\'",
        (user_id, f"%{safe_query}%")
    )

    data = cur.fetchall()
    conn.close()
    return data


def delete_anime_by_id(record_id: int, user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM user_anime WHERE id = ? AND user_id = ?",
        (record_id, user_id)
    )

    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted


def update_watched_episode(record_id: int, user_id: int, watched_episode: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "UPDATE user_anime SET watched_episode = ? WHERE id = ? AND user_id = ?",
        (watched_episode, record_id, user_id)
    )

    updated = cur.rowcount
    conn.commit()
    conn.close()
    return updated

def set_yummy_url(record_id: int, user_id: int, url: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "UPDATE user_anime SET yummy_url = ? WHERE id = ? AND user_id = ?",
        (url, record_id, user_id)
    )

    updated = cur.rowcount
    conn.commit()
    conn.close()
    return updated

# --- фоновая проверка новых серий ---

def get_all_tracked_for_check():
    """Возвращает записи, для которых пора проверить новые серии,
    с учётом персонального интервала пользователя."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT ua.id, ua.user_id, ua.anilist_id, ua.title,
               ua.last_notified_episode, ua.last_episode_check_at,
               COALESCE(us.episode_check_interval_hours, 6)
        FROM user_anime ua
        LEFT JOIN user_settings us ON us.user_id = ua.user_id
    """)

    rows = cur.fetchall()
    conn.close()

    due = []
    for record_id, user_id, anilist_id, title, last_notified, last_check_at, interval_hours in rows:
        if interval_hours <= 0:
            continue
        if hours_since(last_check_at) >= interval_hours:
            due.append((record_id, user_id, anilist_id, title, last_notified))

    return due


def update_episode_check(record_id: int, episode: int, status: str = None, total_episodes: int = None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if status is not None:
        cur.execute(
            """UPDATE user_anime
               SET last_notified_episode = ?, last_episode_check_at = ?,
                   status = ?, total_episodes = ?
               WHERE id = ?""",
            (episode, now_iso(), status, total_episodes, record_id)
        )
    else:
        cur.execute(
            "UPDATE user_anime SET last_notified_episode = ?, last_episode_check_at = ? WHERE id = ?",
            (episode, now_iso(), record_id)
        )

    conn.commit()
    conn.close()


# --- настройки напоминаний пользователя ---

def get_user_settings(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "SELECT episode_check_interval_hours, watch_reminder_interval_hours, last_watch_reminder_at FROM user_settings WHERE user_id = ?",
        (user_id,)
    )
    row = cur.fetchone()

    if row is None:
        cur.execute(
            "INSERT INTO user_settings (user_id) VALUES (?)",
            (user_id,)
        )
        conn.commit()
        row = (6, 0, "")

    conn.close()
    return row


def set_episode_check_interval(user_id: int, hours: int):
    get_user_settings(user_id)  # гарантирует, что строка существует
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE user_settings SET episode_check_interval_hours = ? WHERE user_id = ?",
        (hours, user_id)
    )
    conn.commit()
    conn.close()


def set_watch_reminder_interval(user_id: int, hours: int):
    get_user_settings(user_id)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE user_settings SET watch_reminder_interval_hours = ? WHERE user_id = ?",
        (hours, user_id)
    )
    conn.commit()
    conn.close()


def get_users_due_for_watch_reminder():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "SELECT user_id, watch_reminder_interval_hours, last_watch_reminder_at FROM user_settings WHERE watch_reminder_interval_hours > 0"
    )
    rows = cur.fetchall()
    conn.close()

    due = []
    for user_id, interval_hours, last_sent_at in rows:
        if hours_since(last_sent_at) >= interval_hours:
            due.append(user_id)

    return due


def update_watch_reminder_sent(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE user_settings SET last_watch_reminder_at = ? WHERE user_id = ?",
        (now_iso(), user_id)
    )
    conn.commit()
    conn.close()


def get_unwatched_for_user(user_id: int):
    """Аниме, где остались непросмотренные вышедшие серии."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """SELECT title, watched_episode, last_notified_episode
           FROM user_anime
           WHERE user_id = ? AND last_notified_episode > watched_episode""",
        (user_id,)
    )
    data = cur.fetchall()
    conn.close()
    return data