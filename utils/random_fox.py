import logging
import aiohttp

# Fallback-изображение лисы на случай недоступности API
FALLBACK_FOX_URL = "https://randomfox.ca/images/1.jpg"


async def fox() -> str | None:
    """Получить случайное изображение лисы. Возвращает URL или fallback при ошибке."""
    url = "https://randomfox.ca/floof/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['image']
                else:
                    logging.warning(f"Fox API error: HTTP {response.status}. Использую fallback.")
                    return FALLBACK_FOX_URL
    except Exception as e:
        logging.warning(f"Fox API request failed: {e}. Использую fallback.")
        return FALLBACK_FOX_URL
