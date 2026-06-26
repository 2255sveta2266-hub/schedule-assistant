"""
yandex_kb_sync.py — синхронизация расписания из SQLite в Yandex AI Studio Vector Store.

Вызывается автоматически из parser/update_schedule.py после каждого обновления
расписания группы. Использует официальный OpenAI-совместимый API Yandex AI Studio
через эндпоинт rest-assistant.api.cloud.yandex.net.

Требуемые переменные в .env:
    YANDEX_API_KEY          — API-ключ сервисного аккаунта Yandex Cloud
    YANDEX_FOLDER_ID        — ID папки в Yandex Cloud
    YANDEX_VECTOR_STORE_ID  — ID Vector Store, созданного вручную в Yandex AI Studio

Файл маппинга group → file_id хранится в data/yandex_file_ids.json.
"""

import json
import sys
import io
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

# Маппинг "название группы → file_id в Yandex" хранится рядом с БД
FILE_IDS_PATH = Path(__file__).resolve().parent.parent / "data" / "yandex_file_ids.json"

# Импортируем настройки — если не заданы, модуль просто ничего не делает
try:
    from config.settings import YANDEX_API_KEY, YANDEX_FOLDER_ID, YANDEX_VECTOR_STORE_ID
except ImportError:
    YANDEX_API_KEY = None
    YANDEX_FOLDER_ID = None
    YANDEX_VECTOR_STORE_ID = None


def _is_configured() -> bool:
    """Проверяет, что все три переменные окружения заданы."""
    return bool(YANDEX_API_KEY and YANDEX_FOLDER_ID and YANDEX_VECTOR_STORE_ID)


def _get_openai_client():
    """Создаёт OpenAI-клиент, настроенный на Yandex AI Studio (Responses API).

    Эндпоинт rest-assistant.api.cloud.yandex.net поддерживает:
    - client.files.create()          — загрузка файлов
    - client.vector_stores.files.*   — управление файлами в Vector Store
    - client.responses.create()      — запросы к модели с file_search
    """
    from openai import OpenAI
    return OpenAI(
        api_key=YANDEX_API_KEY,
        base_url="https://rest-assistant.api.cloud.yandex.net/v1",
        project=YANDEX_FOLDER_ID
    )


def _load_file_ids() -> dict:
    """Читает сохранённый маппинг group_name → file_id из JSON."""
    if FILE_IDS_PATH.exists():
        try:
            return json.loads(FILE_IDS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_file_ids(mapping: dict) -> None:
    """Сохраняет обновлённый маппинг group_name → file_id в JSON."""
    FILE_IDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    FILE_IDS_PATH.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")


def _format_schedule_text(group_name: str) -> str:
    """Форматирует расписание группы из БД в читаемый текст для базы знаний.

    Формат намеренно простой и многословный — это улучшает качество
    семантического поиска: модель лучше находит нужные занятия.
    """
    from services.schedule_service import get_schedule_by_group

    lessons = get_schedule_by_group(group_name)

    if not lessons:
        return f"Расписание группы {group_name}: занятия не найдены."

    # Группируем по дате
    by_date: dict = {}
    for lesson in lessons:
        by_date.setdefault(lesson.date, []).append(lesson)

    lines = [f"Расписание учебной группы {group_name}\n"]

    for date in sorted(by_date.keys()):
        lines.append(f"\nДата: {date}")
        day_lessons = sorted(by_date[date], key=lambda l: l.time_start or "")
        for l in day_lessons:
            time_str = l.time_start or "время не указано"
            lesson_type = l.lesson_type or ""
            type_str = f", {lesson_type}" if lesson_type else ""
            teacher_str = f", преподаватель: {l.teacher}" if l.teacher else ""
            room_str = f", аудитория: {l.room}" if l.room else ""
            subgroup_str = f", подгруппа: {l.subgroup}" if l.subgroup else ""
            lines.append(
                f"  {time_str} — {l.subject}{type_str}{teacher_str}{room_str}{subgroup_str}"
            )

    return "\n".join(lines)


def _delete_old_file(client, group_name: str, file_ids: dict) -> None:
    """Удаляет старый файл группы из Vector Store и из хранилища файлов Yandex.

    Если файл уже удалён или не существует — просто логируем и продолжаем.
    """
    old_file_id = file_ids.get(group_name)
    if not old_file_id:
        return

    # Сначала убираем файл из Vector Store
    try:
        client.vector_stores.files.delete(
            vector_store_id=YANDEX_VECTOR_STORE_ID,
            file_id=old_file_id,
        )
        print(f"[KB Sync] Файл {old_file_id} удалён из Vector Store.")
    except Exception as e:
        print(f"[KB Sync] Не удалось удалить файл из Vector Store: {e}")

    # Затем удаляем сам файл из хранилища
    try:
        client.files.delete(old_file_id)
        print(f"[KB Sync] Файл {old_file_id} удалён из хранилища.")
    except Exception as e:
        print(f"[KB Sync] Не удалось удалить файл из хранилища: {e}")


def _upload_and_attach(client, group_name: str, text: str) -> str | None:
    """Загружает текстовый файл расписания в Yandex и добавляет его в Vector Store.

    Возвращает file_id нового файла или None при ошибке.
    """
    filename = f"schedule_{group_name}.txt"

    # Загружаем файл — передаём как bytes-поток, чтобы избежать временных файлов
    file_bytes = text.encode("utf-8")
    file_stream = io.BytesIO(file_bytes)
    file_stream.name = filename  # OpenAI SDK читает .name для Content-Disposition

    try:
        uploaded = client.files.create(file=file_stream, purpose="assistants")
        file_id = uploaded.id
        print(f"[KB Sync] Файл загружен: {file_id} ({filename})")
    except Exception as e:
        print(f"[KB Sync] Ошибка загрузки файла: {e}")
        return None

    # Добавляем файл в Vector Store
    try:
        client.vector_stores.files.create(
            vector_store_id=YANDEX_VECTOR_STORE_ID,
            file_id=file_id,
        )
        print(f"[KB Sync] Файл {file_id} добавлен в Vector Store {YANDEX_VECTOR_STORE_ID}.")
    except Exception as e:
        print(f"[KB Sync] Ошибка добавления файла в Vector Store: {e}")
        # Файл загружен, но не проиндексирован — всё равно сохраняем id,
        # чтобы при следующем обновлении корректно его удалить
        return file_id

    return file_id


def sync_group_to_cloud(group_name: str) -> None:
    """Основная функция: синхронизирует расписание одной группы с Yandex Vector Store.

    Вызывается из parser/update_schedule.py после commit() в БД.
    При любой ошибке пишет в лог и НЕ бросает исключение — чтобы не прерывать
    основной процесс парсинга.
    """
    if not _is_configured():
        print("[KB Sync] Пропуск: YANDEX_API_KEY / YANDEX_FOLDER_ID / YANDEX_VECTOR_STORE_ID не заданы.")
        return

    print(f"[KB Sync] Синхронизация группы {group_name}...")

    try:
        client = _get_openai_client()
        file_ids = _load_file_ids()

        # Шаг 1: удаляем старую версию файла
        _delete_old_file(client, group_name, file_ids)

        # Шаг 2: форматируем свежее расписание из БД
        schedule_text = _format_schedule_text(group_name)

        # Шаг 3: загружаем новый файл и добавляем в Vector Store
        new_file_id = _upload_and_attach(client, group_name, schedule_text)

        # Шаг 4: сохраняем новый маппинг
        if new_file_id:
            file_ids[group_name] = new_file_id
            _save_file_ids(file_ids)
            print(f"[KB Sync] ✅ Группа {group_name} синхронизирована. file_id={new_file_id}")
        else:
            # Если загрузка не удалась — удаляем устаревший id из маппинга
            file_ids.pop(group_name, None)
            _save_file_ids(file_ids)
            print(f"[KB Sync] ⚠️  Группа {group_name}: синхронизация не удалась.")

    except Exception as e:
        print(f"[KB Sync] ❌ Неожиданная ошибка при синхронизации {group_name}: {e}")
