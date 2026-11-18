# Лабораторная 1 — Сбор данных из соцсетей

Сбор постов [vk.ru/samara_university](https://vk.ru/samara_university) за 01.08–31.08.2026 через VK API (`wall.get`).

## Запуск

```bash
./setup_linux        # разово: создаёт .venv, ставит зависимости, копирует .env
./start_linux
```

## Настройка

В `.env` (из `.env.example`):

- `VK_USER_TOKEN` — токен из [vkhost](https://vkhost.github.io) (scope wall,groups)
- `VK_GROUP_SCREEN_NAME` — короткое имя сообщества
- `DATE_FROM` / `DATE_TO` — период, `YYYY-MM-DD`
- `OUTPUT_FORMAT` — `json` (по умолчанию) | `parquet` | `both`

## Результат

`data/posts_<от>_<до>.json` и/или `.parquet` — по 40 постов, схема поста плоская:

`post_id, post_url, post_type, owner_id, from_id, publish_time, edited_time, text, view_count, like_count, comment_count, repost_count, attachment_count, attachment_types, attachment_urls, marked_as_ads, pinned, reposted_from`

В JSON типы/URL вложений — списки, в parquet — строка через `;`.
