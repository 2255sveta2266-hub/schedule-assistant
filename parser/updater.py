import sys
from pathlib import Path
import threading
import time

sys.path.append(str(Path(__file__).resolve().parent.parent))

import schedule

from parser.group_finder import get_groups
from parser.update_schedule import update_schedule
from config.parser_config import DEFAULT_MONTH, DEFAULT_YEAR

DEPARTMENT_ID = 683

# Файл-маркер — сохраняем время последнего обновления
LAST_UPDATE_FILE = Path(__file__).resolve().parent.parent / "data" / "last_update.txt"
UPDATE_INTERVAL_HOURS = 24


def _get_last_update_time():
    """Читаем время последнего обновления из файла"""
    try:
        if LAST_UPDATE_FILE.exists():
            return float(LAST_UPDATE_FILE.read_text().strip())
    except Exception:
        pass
    return 0


def _save_last_update_time():
    """Сохраняем текущее время как время последнего обновления"""
    try:
        LAST_UPDATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        LAST_UPDATE_FILE.write_text(str(time.time()))
    except Exception as e:
        print(f"[Updater] Не удалось сохранить время обновления: {e}")


def _is_update_needed():
    """Проверяем нужно ли обновлять — если прошло больше 24 часов"""
    elapsed_hours = (time.time() - _get_last_update_time()) / 3600
    return elapsed_hours >= UPDATE_INTERVAL_HOURS


def _do_update():
    """Скачивает расписание всех групп, сохраняет в БД и синхронизирует в Vector Store"""
    print(f"\n[Updater] Получаем список всех групп подразделения {DEPARTMENT_ID}...")

    groups = get_groups(DEPARTMENT_ID)

    if not groups:
        print("[Updater] ❌ Группы не найдены! Проверь подключение к интернету.")
        return

    print(f"[Updater] Найдено групп: {len(groups)}")
    print("[Updater] Начинаем обновление расписания...\n")

    success = 0
    failed = 0

    for group_name, group_id in groups.items():
        try:
            print(f"[Updater] ▶ {group_name}")
            update_schedule(
                group_name,
                group_id=group_id,
                month=DEFAULT_MONTH,
                year=DEFAULT_YEAR
            )
            success += 1
        except Exception as e:
            print(f"[Updater] ❌ Ошибка при обновлении {group_name}: {e}")
            failed += 1

    _save_last_update_time()
    print(f"\n[Updater] ✅ Обновление завершено! Успешно: {success}, с ошибками: {failed}\n")


def run_auto_update():
    """
    Запускает планировщик обновления в фоновом потоке.

    Использует библиотеку schedule для управления расписанием задач.
    - При старте: если данные устарели (>24ч) — обновляет сразу.
    - Далее: запускает обновление каждый день в 03:00.
    - Бот стартует мгновенно, обновление идёт в фоне.
    """

    # Регистрируем задачу в планировщике — каждый день в 03:00
    schedule.every().day.at("03:00").do(_do_update)
    print("[Updater] Планировщик настроен: обновление расписания каждый день в 03:00.")

    def loop():
        # При старте проверяем актуальность данных
        if _is_update_needed():
            print("[Updater] Данные устарели — запускаем обновление немедленно...")
            _do_update()
        else:
            last = _get_last_update_time()
            elapsed = (time.time() - last) / 3600
            remaining = UPDATE_INTERVAL_HOURS - elapsed
            print(f"[Updater] Данные актуальны. Следующее плановое обновление через {remaining:.1f} ч. (в 03:00).")

        # Основной цикл планировщика — проверяем каждую минуту
        while True:
            schedule.run_pending()
            time.sleep(60)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    print("[Updater] Фоновый планировщик запущен.")


if __name__ == "__main__":
    # При прямом запуске — принудительное обновление без планировщика
    _do_update()