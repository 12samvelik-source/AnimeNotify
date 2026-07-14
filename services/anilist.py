import aiohttp

URL = "https://graphql.anilist.co"


async def search_anime(name: str):
    query = """
    query ($search: String) {
      Page(perPage: 5) {
        media(search: $search, type: ANIME) {
          id
          episodes
          status
          format
          coverImage { large }
          title { romaji english native }
          nextAiringEpisode { episode airingAt }
        }
      }
    }
    """
    variables = {"search": name}

    async with aiohttp.ClientSession() as session:
        async with session.post(URL, json={"query": query, "variables": variables}) as response:
            data = await response.json()
            return data["data"]["Page"]["media"]


async def get_anime_details(anilist_id: int):
    query = """
    query ($id: Int) {
      Media(id: $id, type: ANIME) {
        id
        episodes
        status
        nextAiringEpisode { episode airingAt }
      }
    }
    """
    variables = {"id": anilist_id}

    async with aiohttp.ClientSession() as session:
        async with session.post(URL, json={"query": query, "variables": variables}) as response:
            data = await response.json()
            return data["data"]["Media"]


STATUS_LABELS = {
    "RELEASING": "🟢 Онгоинг",
    "FINISHED": "✅ Завершён",
    "NOT_YET_RELEASED": "⏳ Анонс",
    "CANCELLED": "❌ Отменён",
    "HIATUS": "⏸ Приостановлен",
}


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status or "—")


def current_known_episode(anime: dict) -> int:
    """Номер последней вышедшей серии (не считая ту, что ещё выходит)."""
    next_airing = anime.get("nextAiringEpisode")
    if next_airing:
        return max(next_airing["episode"] - 1, 0)
    return anime.get("episodes") or 0