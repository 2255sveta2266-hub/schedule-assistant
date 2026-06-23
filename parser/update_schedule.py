import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from parser.schedule_parser import (
    get_month_dates,
    get_lessons_for_day
)

from parser.group_finder import find_group_id

from services.schedule_service import (
    add_schedule,
    clear_schedule
)


def update_schedule(group_name, department_id=683):

    clear_schedule()

    group_id = find_group_id(group_name, department_id)

    if not group_id:
        print("Группа не найдена")
        return

    dates = get_month_dates(group_id)

    total_lessons = 0
    seen = set()

    for date, info in dates.items():

        full_url = "https://www.istu.edu" + info["link"]
        lessons = get_lessons_for_day(full_url)

        for lesson in lessons:

            key = (
                group_name,
                date,
                lesson["time"],
                lesson["subject"],
                lesson["teacher"]
            )

            if key in seen:
                continue

            seen.add(key)

            add_schedule(
                group_name=group_name,
                teacher=lesson["teacher"],
                subject=lesson["subject"],
                date=date,
                time_start=lesson["time"],
                time_end="",
                room=lesson["room"]
            )

            total_lessons += 1

        print(f"{date} -> {len(lessons)} занятий")

    print(f"\nВсего сохранено: {total_lessons}")


if __name__ == "__main__":
    update_schedule("АСУб-25-1")