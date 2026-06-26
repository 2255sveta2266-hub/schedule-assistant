"""
yandex_assistant.py — основная логика обработки сообщений пользователя.

Архитектура:
- Для точечных запросов (группа+дата, преподаватель) — данные берём из SQLite
  и отправляем напрямую в YandexGPT как контекст. Так нет дублирования из Vector Store.
- Vector Store / file_search используется только для свободных вопросов
  без чёткой группы и даты.
- При отсутствии ключей — fallback на форматированный ответ из локальной БД.
"""

import re
from datetime import datetime, timedelta

from assistant.knowledge_base import (
    find_group_schedule,
    find_teacher_schedule,
    find_date_schedule,
    find_group_day_schedule
)

try:
    from config.settings import YANDEX_API_KEY, YANDEX_FOLDER_ID, YANDEX_VECTOR_STORE_ID
except ImportError:
    YANDEX_API_KEY = None
    YANDEX_FOLDER_ID = None
    YANDEX_VECTOR_STORE_ID = None


HELP_TEXT = """👋 Привет! Я бот-помощник по расписанию ИРНИТУ.

Что я умею:
📚 Расписание группы — напиши название: АСУб-25-1
👨‍🏫 Расписание преподавателя — напиши: преподаватель Павлова
📅 Расписание на дату — напиши: 01.04.2026
📆 На сегодня — напиши: сегодня
📆 На завтра — напиши: завтра
🔄 Сменить группу — напиши: сменить группу"""

SYSTEM_PROMPT = (
    "Ты помощник студента ИРНИТУ. "
    "Тебе передаётся расписание занятий. "
    "Выведи его аккуратно, каждое занятие СТРОГО ОДИН РАЗ. "
    "Не повторяй занятия. Не придумывай. "
    "Формат без Markdown:\n"
    "📅 Дата\n🕗 Время\n📖 Предмет (тип)\n👨‍🏫 Преподаватель\n🏫 Аудитория\n\n"
    "Если занятий нет — напиши об этом кратко."
)


def _get_client():
    from openai import OpenAI
    return OpenAI(
        api_key=YANDEX_API_KEY,
        base_url="https://rest-assistant.api.cloud.yandex.net/v1",
        project=YANDEX_FOLDER_ID,
    )


def _ask_with_context(user_text: str, schedule_context: str) -> str:
    """
    Отправляет запрос в YandexGPT с расписанием напрямую как контекст.
    НЕ использует Vector Store — данные уже точные из SQLite.
    Это главный способ для запросов с группой+датой.
    """
    if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
        return schedule_context

    import requests as req
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.1,
            "maxTokens": 800,
        },
        "messages": [
            {"role": "system", "text": SYSTEM_PROMPT},
            {"role": "user", "text": f"{user_text}\n\nРасписание:\n{schedule_context}"},
        ],
    }
    try:
        resp = req.post(url, json=body, headers=headers, timeout=15)
        data = resp.json()
        return data["result"]["alternatives"][0]["message"]["text"]
    except Exception as e:
        print(f"[YandexGPT] Ошибка direct-запроса: {e}")
        return schedule_context


def _ask_with_file_search(user_text: str, fallback: str) -> str:
    """
    Отправляет свободный запрос в Responses API с file_search (Vector Store).
    Используется только когда нет чёткой группы и даты.
    """
    if not YANDEX_API_KEY or not YANDEX_FOLDER_ID or not YANDEX_VECTOR_STORE_ID:
        return fallback

    try:
        client = _get_client()
        model_uri = f"gpt://{YANDEX_FOLDER_ID}/yandexgpt/latest"

        response = client.responses.create(
            model=model_uri,
            instructions=(
                "Ты помощник студента ИРНИТУ. "
                "Ищи информацию через file_search. "
                "Каждое занятие показывай один раз. "
                "Без Markdown. Формат: 📅 дата, 🕗 время, 📖 предмет, 👨‍🏫 преподаватель, 🏫 аудитория."
            ),
            input=[{"role": "user", "content": user_text}],
            tools=[{
                "type": "file_search",
                "vector_store_ids": [YANDEX_VECTOR_STORE_ID],
                "max_num_results": 2,
            }],
            temperature=0.1,
            max_output_tokens=800,
        )

        # Берём только первый текстовый блок
        if hasattr(response, "output_text") and response.output_text:
            return response.output_text.strip()

        for item in response.output:
            if getattr(item, "type", None) == "message":
                for block in item.content:
                    if getattr(block, "type", None) == "output_text":
                        text = block.text.strip()
                        if text:
                            return text

    except Exception as e:
        print(f"[YandexGPT] Ошибка file_search-запроса: {e}")

    return fallback


def process_message(text: str) -> str:
    text_stripped = text.strip()
    text_lower = text_stripped.lower()

    if text_lower in ("помощь", "help", "/start", "start", "привет", "начать", "хелп"):
        return HELP_TEXT

    # Ищем группу в тексте
    group_match = re.search(r"[А-ЯЁа-яё]+-\d{2}-\d+", text_stripped, re.IGNORECASE)
    group_name = None
    if group_match:
        raw = group_match.group()
        parts = raw.split("-")
        letters = parts[0]
        if len(letters) > 1:
            letters = letters[:-1].upper() + letters[-1].lower()
        group_name = "-".join([letters] + parts[1:])

    # Сегодня — берём из SQLite, отправляем напрямую (без Vector Store)
    if "сегодня" in text_lower:
        today = datetime.now().strftime("%d.%m.%Y")
        if group_name:
            raw_data = find_group_day_schedule(group_name, today)
            query = f"Расписание группы {group_name} на {today}."
        else:
            raw_data = find_date_schedule(today)
            query = f"Расписание на {today}."
        return _ask_with_context(query, raw_data)

    # Завтра — аналогично
    if "завтра" in text_lower:
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
        if group_name:
            raw_data = find_group_day_schedule(group_name, tomorrow)
            query = f"Расписание группы {group_name} на {tomorrow}."
        else:
            raw_data = find_date_schedule(tomorrow)
            query = f"Расписание на {tomorrow}."
        return _ask_with_context(query, raw_data)

    # Преподаватель — из SQLite напрямую
    teacher_match = re.search(
        r"(?:расписание\s+)?(?:преподавател[яь]|препода?|учител[яь])\s+([А-ЯЁа-яё]+)",
        text_stripped, re.IGNORECASE,
    )
    if teacher_match:
        teacher = teacher_match.group(1)
        raw_data = find_teacher_schedule(teacher)
        query = f"Расписание преподавателя {teacher}."
        return _ask_with_context(query, raw_data)

    # Конкретная дата — из SQLite напрямую
    date_match = re.search(r"\d{2}\.\d{2}\.\d{4}", text_stripped)
    if date_match:
        db_date = date_match.group()
        if group_name:
            raw_data = find_group_day_schedule(group_name, db_date)
            query = f"Расписание группы {group_name} на {db_date}."
        else:
            raw_data = find_date_schedule(db_date)
            query = f"Расписание на {db_date}."
        return _ask_with_context(query, raw_data)

    # Группа без даты — из SQLite напрямую
    if group_name:
        raw_data = find_group_schedule(group_name)
        query = f"Расписание группы {group_name}."
        return _ask_with_context(query, raw_data)

    # Свободный вопрос без группы и даты — идёт в Vector Store
    return _ask_with_file_search(
        text_stripped,
        fallback=(
            "Не понял запрос 😕\n\n"
            "Попробуй:\n"
            "• Группу: АСУб-25-1\n"
            "• Дату: 01.04.2026\n"
            "• Написать: сегодня\n"
            "• Написать: завтра\n"
            "• Написать: помощь"
        )
    )