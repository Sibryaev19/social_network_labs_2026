# Лабораторная 1 — Сбор данных из социальных сетей

Сбор постов сообщества Самарского Университета ([vk.ru/samara_university](https://vk.ru/samara_university))
за период **01.08.2026 – 31.08.2026** через официальный VK API (`wall.get`).

## Запуск

- Linux: `./start_linux`
- Windows: `start_windows.bat`

При первом запуске скрипт сам создаст `.venv`, поставит зависимости
(`requests`) и скопирует `.env` из `.env.example`, если `.env` нет.

## Настройка

В `.env`:

| Переменная | Что это |
|---|---|
| `VK_SERVICE_TOKEN` | сервисный ключ приложения с dev.vk.com (основной вариант) |
| `VK_USER_TOKEN` | пользовательский ключ (OAuth VK ID) — запасной вариант |
| `VK_API_VERSION` | версия API (по умолчанию 5.199) |
| `VK_GROUP_SCREEN_NAME` | короткое имя сообщества |
| `DATE_FROM` / `DATE_TO` | период сбора, `YYYY-MM-DD`, включительно |
| `POSTS_PER_REQUEST` | постов за один запрос wall.get (макс. 100) |

**Важно:** токен не вставлять в README/чат/репозиторий. Если проект попадёт
в git — добавить в `.gitignore`: `.env`, `.venv/`, `__pycache__/`.

## Результат

`data/posts_<DATE_FROM>_<DATE_TO>.json` — JSON вида:

```json
{
  "group": "samara_university",
  "period": ["2026-08-01", "2026-08-31"],
  "posts": [
    {"id": 123, "date": 1754092800, "text": "...",
     "likes": {"count": 12}, "comments": {"count": 3},
     "reposts": {"count": 1}, "views": {"count": 456}}
  ]
}
```

## Структура

```
lab1/
├── start.py            # точка входа: грузит .env, запускает src.main
├── start_linux         # обёртка запуска для Linux
├── start_windows.bat   # обёртка запуска для Windows
├── setup/setup.py      # создание .venv и установка зависимостей
├── src/
│   ├── config.py       # параметры из .env
│   ├── vk/             # модуль VK API (копируется в lab2/lab3 как есть)
│   │   ├── __init__.py
│   │   └── client.py   # VkApi: лимиты, ретраи, wall.get, wall.getComments
│   └── main.py         # сбор за период -> data/*.json
├── data/               # результат
└── .env / .env.example
```

## Модуль VK API (src/vk)

Общий для всех VK-лаб. Подключение в два строки:

```python
from src.vk import VkApi
api = VkApi(token, api_version)          # токен из .env (см. src/config.py)
posts = api.wall_posts(owner_id, ts_from, ts_to)
comments = api.post_comments(owner_id, post_id)
```

Внутри: паузы под лимит API (3–5 rps), автоповтор при ошибках 6/9/10,
пагинация по периоду (останавливается, когда посты уходят ниже даты).
