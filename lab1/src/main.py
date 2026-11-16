"""Сборка: получить посты за период из .env и сохранить в JSON."""
import datetime as dt
import json
import os

from . import config
from .vk import VkApi

FIELDS_OF_INTEREST = ["date", "text", "likes", "comments", "reposts", "views"]


def _to_ts(date_str, end_of_day=False):
    d = dt.date.fromisoformat(date_str)
    if end_of_day:
        return int(dt.datetime(d.year, d.month, d.day, 23, 59, 59).timestamp())
    return int(dt.datetime(d.year, d.month, d.day).timestamp())


def _trim(post):
    """Оставляем поля, нужные по заданию (+ id для ссылок на пост)."""
    result = {"id": post.get("id")}
    for key in FIELDS_OF_INTEREST:
        value = post.get(key)
        if value is not None:
            result[key] = value
    return result


def main():
    date_from_ts = _to_ts(config.DATE_FROM)
    date_to_ts = _to_ts(config.DATE_TO, end_of_day=True)

    api = VkApi(config.token(), config.API_VERSION)
    owner_id = api.group_id(config.GROUP_SCREEN_NAME)
    print(f"Сообщество {config.GROUP_SCREEN_NAME}: owner_id={owner_id}")

    posts = api.wall_posts(
        owner_id, date_from_ts, date_to_ts,
        per_request=config.POSTS_PER_REQUEST,
        on_progress=lambda n, offset: print(
            f"  собрано {n} постов (offset {offset})..."),
    )

    data = {
        "group": config.GROUP_SCREEN_NAME,
        "period": [config.DATE_FROM, config.DATE_TO],
        "posts": [_trim(p) for p in posts],
    }

    os.makedirs(config.DATA_DIR, exist_ok=True)
    out = os.path.join(
        config.DATA_DIR,
        f"posts_{config.DATE_FROM}_{config.DATE_TO}.json",
    )
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Готово: {len(posts)} постов -> {out}")
    return 0


if __name__ == "__main__":
    main()
