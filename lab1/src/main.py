"""Сборка: получить посты за период из .env и сохранить в JSON/Parquet.

Схема поста плоская (без вложенных словарей):
    post_id, post_url, post_type, owner_id, from_id, publish_time,
    edited_time, text, view_count, like_count, comment_count,
    repost_count, attachment_count, attachment_types, attachment_urls,
    marked_as_ads, pinned, reposted_from
Перечисления (типы и URL вложений):
    в Parquet — строка через «;», в JSON — список.
Формат вывода — .env: OUTPUT_FORMAT = json | parquet | both (дефолт json).
"""
import datetime as dt
import json
import os

from . import config
from .vk import VkApi

VK_BASE = "https://vk.ru"


def _to_ts(date_str, end_of_day=False):
    d = dt.date.fromisoformat(date_str)
    if end_of_day:
        return int(dt.datetime(d.year, d.month, d.day, 23, 59, 59).timestamp())
    return int(dt.datetime(d.year, d.month, d.day).timestamp())


def _fmt_ts(ts):
    """Unix -> 'YYYY-MM-DD HH:MM:SS' (локальное время машины сбора)."""
    if not ts:
        return None
    return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def _wall_link(owner_id, post_id):
    return f"{VK_BASE}/wall{owner_id}_{post_id}"


def _attachment_urls(post):
    """URL вложений в том же порядке, что attachment_types.

    photo — ссылка на максимальный размер; video — страница видео
    (файл wall.get не отдаёт); link/doc — url. Нет адреса — пустая строка.
    """
    urls = []
    for att in post.get("attachments", []):
        kind, obj = att.get("type"), att.get(att.get("type"), {})
        url = ""
        if kind == "photo":
            sizes = obj.get("sizes", [])
            if sizes:
                url = max(sizes, key=lambda s: s.get("width", 0)).get("url", "")
        elif kind == "video":
            url = f"{VK_BASE}/video{obj.get('owner_id')}_{obj.get('id')}"
        elif kind in ("link", "doc", "audio", "note"):
            url = obj.get("url", "") or ""
        urls.append(url)
    return urls


def _count(field):
    """Счётчик из вложенного словаря (likes.count и т.п.)."""
    value = field.get("count") if isinstance(field, dict) else None
    return value


def _trim(post, owner_id):
    """Пост -> плоский словарь по схеме из докстринга модуля."""
    post_id = post.get("id")
    attachments = post.get("attachments", [])
    # типы — уникальные (порядок первого появления), URL — все по одному на вложение
    att_types = list(dict.fromkeys(a.get("type", "") for a in attachments))
    att_urls = _attachment_urls(post)

    copy = (post.get("copy_history") or [{}])[0]
    return {
        "post_id": post_id,
        "post_url": _wall_link(owner_id, post_id),
        "post_type": post.get("post_type"),
        "owner_id": post.get("owner_id", owner_id),
        "from_id": post.get("from_id"),
        "publish_time": _fmt_ts(post.get("date")),
        "edited_time": _fmt_ts(post.get("edited")),
        "text": post.get("text", ""),
        "view_count": _count(post.get("views")),
        "like_count": _count(post.get("likes")),
        "comment_count": _count(post.get("comments")),
        "repost_count": _count(post.get("reposts")),
        "attachment_count": len(attachments),
        "attachment_types": att_types,
        "attachment_urls": att_urls,
        "marked_as_ads": post.get("marked_as_ads"),
        "pinned": post.get("pinned"),
        "reposted_from": (_wall_link(copy.get("owner_id"), copy.get("id"))
                          if copy.get("id") else None),
    }


def _save_json(posts, out_path):
    data = {
        "group": config.GROUP_SCREEN_NAME,
        "period": [config.DATE_FROM, config.DATE_TO],
        "posts": posts,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Готово: {len(posts)} постов -> {out_path}")


def _save_parquet(posts, out_path):
    import pandas as pd  # тяжёлый импорт — только если выбран parquet

    rows = []
    for post in posts:
        row = dict(post)
        for key in ("attachment_types", "attachment_urls"):
            row[key] = ";".join(row[key])
        rows.append(row)
    pd.DataFrame(rows).to_parquet(out_path, index=False)
    print(f"Готово: {len(posts)} постов -> {out_path}")


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

    flat = [_trim(p, owner_id) for p in posts]

    os.makedirs(config.DATA_DIR, exist_ok=True)
    stem = f"posts_{config.DATE_FROM}_{config.DATE_TO}"
    fmt = config.OUTPUT_FORMAT
    if fmt in ("json", "both"):
        _save_json(flat, os.path.join(config.DATA_DIR, stem + ".json"))
    if fmt in ("parquet", "both"):
        _save_parquet(flat, os.path.join(config.DATA_DIR, stem + ".parquet"))
    return 0


if __name__ == "__main__":
    main()
