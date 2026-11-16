"""Чтение параметров задачи из .env (переменных окружения)."""
import os

API_URL = "https://api.vk.ru/method/"


def _get(key, default=None):
    value = os.environ.get(key, default)
    if value in (None, ""):
        raise RuntimeError(f"Не задан параметр {key} в .env")
    return value


def _get_int(key, default):
    return int(os.environ.get(key, default))


# Токен: сначала сервисный, если пусто — пользовательский
def token():
    value = os.environ.get("VK_SERVICE_TOKEN") or os.environ.get("VK_USER_TOKEN")
    if not value:
        raise RuntimeError(
            "Не задан ни VK_SERVICE_TOKEN, ни VK_USER_TOKEN в .env"
        )
    return value


API_VERSION = _get("VK_API_VERSION", "5.199")
GROUP_SCREEN_NAME = _get("VK_GROUP_SCREEN_NAME", "samara_university")

# Период сбора, включительно, формат YYYY-MM-DD
DATE_FROM = _get("DATE_FROM")
DATE_TO = _get("DATE_TO")

POSTS_PER_REQUEST = _get_int("POSTS_PER_REQUEST", 100)

# Куда сохранить результат
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
