import aiohttp

BASE_URL = "https://shikimori.one/api/animes"
HEADERS = {"User-Agent": "AnimeNotifyBot/1.0"}


async def get_russian_title(query: str) -> str | None:
    params = {"search": query, "limit": 1}

    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(BASE_URL, params=params) as response:
                if response.status != 200:
                    return None
                data = await response.json()
    except Exception:
        return None

    if not data:
        return None

    russian = data[0].get("russian")
    return russian or None