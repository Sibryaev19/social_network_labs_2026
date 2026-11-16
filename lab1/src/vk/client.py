"""Клиент VK API для лабораторных: токен, лимиты, ретраи, пагинация.

Подключение:
    from src.vk import VkApi
    api = VkApi(token, api_version)
    owner_id = api.group_id("samara_university")
    posts = api.wall_posts(owner_id, date_from_ts, date_to_ts)

Токен берётся из .env лабы: VK_SERVICE_TOKEN или VK_USER_TOKEN (кто задан).
Ограничения API соблюдаются автоматически: пауза между запросами,
повторные попытки при ошибках 6/9 (слишком часто / flood control).
"""
import time

import requests

API_URL = "https://api.vk.ru/method/"

# Ошибки, при которых стоит повторить запрос: 6 — слишком часто,
# 9 — flood control, 10 — внутренняя ошибка сервера.
_RETRY_CODES = {6, 9, 10}


class VkApiError(RuntimeError):
    """Ошибка вызова метода VK API (не повторяемая или после ретраев)."""


class VkApi:
    def __init__(self, token, version="5.199", pause=0.4, max_retries=3,
                 timeout=30):
        self.token = token
        self.version = version
        self.pause = pause          # пауза между запросами, сек (лимит 3-5 rps)
        self.max_retries = max_retries
        self.timeout = timeout
        self._last_call = 0.0

    # ---- базовый вызов -------------------------------------------------

    def _throttle(self):
        wait = self.pause - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.monotonic()

    def call(self, method, **params):
        """Вызов метода API. Возвращает response; ошибка — исключением.

        Повторяет запрос при лимитных ошибках (6/9/10) с нарастающей
        паузой; остальные ошибки VK API — VkApiError сразу.
        """
        params.setdefault("v", self.version)
        params.setdefault("access_token", self.token)
        last_error = None
        for attempt in range(self.max_retries):
            self._throttle()
            resp = requests.post(API_URL + method, data=params,
                                 timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            if "error" not in data:
                return data["response"]
            error = data["error"]
            if error.get("error_code") in _RETRY_CODES:
                last_error = error
                time.sleep(1 + attempt)
                continue
            raise VkApiError(
                f"{method}: ошибка {error.get('error_code')} — "
                f"{error.get('error_msg')}"
            )
        raise VkApiError(
            f"{method}: не прошёл за {self.max_retries} попытки "
            f"(последняя ошибка {last_error})"
        )

    # ---- типовые операции лаб ------------------------------------------

    def group_id(self, screen_name):
        """Отрицательный owner_id сообщества по короткому имени."""
        info = self.call("groups.getById", group_ids=screen_name,
                         fields="members_count")
        groups = info["groups"] if isinstance(info, dict) else info
        return -groups[0]["id"]

    def wall_posts(self, owner_id, date_from_ts, date_to_ts,
                   per_request=100, on_progress=None):
        """Все посты на стене за период [date_from_ts; date_to_ts] включительно.

        Посты идут от новых к старым: листаем offset'ами и останавливаемся,
        как только ушли ниже нижней границы периода.
        """
        posts = []
        offset = 0
        while True:
            batch = self.call("wall.get", owner_id=owner_id,
                              count=per_request, offset=offset)
            items = batch.get("items", [])
            if not items:
                break

            for item in items:
                date = item.get("date", 0)
                if date > date_to_ts:
                    continue  # пост новее периода
                if date < date_from_ts:
                    return posts  # дальше всё старее — можно стоп
                posts.append(item)

            offset += len(items)
            if on_progress:
                on_progress(len(posts), offset)

            if len(items) < per_request:
                break
        return posts

    def post_comments(self, owner_id, post_id, per_request=100,
                      extended=0):
        """Все комментарии к посту (со вложенностью первого уровня).

        Для лаб с анализом обсуждений. Возвращает список items.
        """
        comments = []
        offset = 0
        while True:
            batch = self.call("wall.getComments", owner_id=owner_id,
                              post_id=post_id, need_likes=1,
                              count=per_request, offset=offset,
                              extended=extended, thread_items_count=10)
            items = batch.get("items", [])
            if not items:
                break
            comments.extend(items)
            offset += len(items)
            if len(items) < per_request:
                break
        return comments

    def users(self, user_ids, fields=""):
        """Информация о пользователях (users.get)."""
        return self.call("users.get", user_ids=",".join(map(str, user_ids)),
                         fields=fields)
