import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from parser.schedule_parser import get_month_dates, get_lessons_for_day
from parser.group_finder import find_group_id
from services.schedule_service import clear_schedule
from database.db_manager import SessionLocal, create_database
from database.models import Schedule
from config.parser_config import DEFAULT_MONTH, DEFAULT_YEAR
from assistant.yandex_kb_sync import sync_group_to_cloud


def update_schedule(group_name, group_id=None, department_id=683, month=DEFAULT_MONTH, year=DEFAULT_YEAR):

    print(f"Обновление расписания для группы: {group_name}")

    create_database()

    if not group_id:
        group_id = find_group_id(group_name, department_id)

    if not group_id:
        print(f"Группа '{group_name}' не найдена!")
        return

    print(f"GROUP ID: {group_id}")

    clear_schedule(group_name)
    print("Старое расписание очищено.")

    dates = get_month_dates(group_id, month=month, year=year)

    # Защита: иногда API возвращает список вместо словаря (пустое расписание)
    if not isinstance(dates, dict):
        print(f"Расписание для группы {group_name} недоступно (пустой ответ от сайта).")
        return

    if not dates:
        print(f"На выбранный месяц занятий нет.")
        return

    total_saved = 0
    session = SessionLocal()

    for date, info in dates.items():
        full_url = "https://www.istu.edu" + info["link"]
        print(f"Дата: {date}  ", end="")

        lessons = get_lessons_for_day(full_url, target_date=date)
        print(f"Занятий: {len(lessons)}")

        for lesson in lessons:
            time_parts = lesson["time"].split("-") if "-" in lesson["time"] else [lesson["time"], ""]
            time_start = time_parts[0].strip()
            time_end = time_parts[1].strip() if len(time_parts) > 1 else ""

            session.add(Schedule(
                group_name=group_name,
                teacher=lesson["teacher"],
                subject=lesson["subject"],
                date=date,
                time_start=time_start,
                time_end=time_end,
                room=lesson["room"],
                subgroup=lesson.get("subgroup", ""),
                lesson_type=lesson.get("lesson_type", "")
            ))
            total_saved += 1

    session.commit()
    session.close()

    print(f"\n Готово! Сохранено записей: {total_saved}")

    # Синхронизируем обновлённое расписание с Yandex AI Studio Vector Store.
    # Выполняется после commit() — данные в БД уже актуальны.
    # Ошибки синхронизации не прерывают основной процесс парсинга.
    sync_group_to_cloud(group_name)


if __name__ == "__main__":
    update_schedule("АСУб-25-1")