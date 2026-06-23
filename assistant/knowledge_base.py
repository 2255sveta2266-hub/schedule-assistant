from services.schedule_service import (
    get_schedule_by_group,
    get_schedule_by_date,
    get_schedule_by_teacher
)


def find_group_schedule(group_name):

    lessons = get_schedule_by_group(group_name)

    if not lessons:
        return "Расписание не найдено."

    answer = f"📚 Расписание группы {group_name}\n\n"

    for l in lessons:
        answer += (
            f"{l.date}\n"
            f"{l.time_start}\n"
            f"{l.subject}\n"
            f"{l.teacher}\n"
            f"{l.room}\n\n"
        )

    return answer


def find_teacher_schedule(teacher):

    lessons = get_schedule_by_teacher(teacher)

    if not lessons:
        return "Преподаватель не найден."

    answer = f"👨‍🏫 Расписание {teacher}\n\n"

    for l in lessons:
        answer += (
            f"{l.date}\n"
            f"{l.time_start}\n"
            f"{l.subject}\n"
            f"{l.group_name}\n"
            f"{l.room}\n\n"
        )

    return answer


def find_date_schedule(date):

    lessons = get_schedule_by_date(date)

    if not lessons:
        return "На эту дату нет занятий."

    answer = f"📅 Расписание на {date}\n\n"

    for l in lessons:
        answer += (
            f"{l.time_start}\n"
            f"{l.subject}\n"
            f"{l.teacher}\n"
            f"{l.group_name}\n\n"
        )

    return answer