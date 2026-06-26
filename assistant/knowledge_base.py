from datetime import datetime
from services.schedule_service import (
    get_schedule_by_group,
    get_schedule_by_date,
    get_schedule_by_teacher,
    get_schedule_by_group_and_date
)


def parse_date(date_str):
    """Сортировка дат в формате дд.мм.гггг"""
    try:
        return datetime.strptime(date_str, "%d.%m.%Y")
    except Exception:
        return datetime.min


def format_date_display(date_str):
    """Дата уже в формате дд.мм.гггг — возвращаем как есть"""
    return date_str


def sort_time(t):
    """Сортировка по времени вида '8:15', '10:00'"""
    try:
        h, m = t.split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return 9999


def deduplicate(lessons):
    """Убираем дубли по (время, предмет)"""
    seen = set()
    result = []
    for l in lessons:
        key = (l.time_start, l.subject)
        if key not in seen:
            seen.add(key)
            result.append(l)
    return result


# Эмодзи для типов занятий
LESSON_TYPE_EMOJI = {
    "лекция": "📖",
    "практика": "✏️",
    "лабораторная": "🔬",
    "семинар": "💬",
    "экзамен": "📝",
    "зачёт": "✅",
    "консультация": "💡",
}


def format_lesson(l, show_group=False, show_date=False):
    parts = []

    if show_date and l.date:
        parts.append(f"📅 {format_date_display(l.date)}")

    if l.time_start:
        parts.append(f"🕐 {l.time_start}")

    # Тип занятия с эмодзи
    lesson_type = getattr(l, "lesson_type", "") or ""
    type_emoji = LESSON_TYPE_EMOJI.get(lesson_type.lower(), "📚")
    type_str = f" ({lesson_type})" if lesson_type else ""
    parts.append(f"{type_emoji} {l.subject}{type_str}")

    if l.teacher:
        parts.append(f"👨‍🏫 {l.teacher}")

    if show_group and l.group_name:
        parts.append(f"👥 {l.group_name}")

    if l.room:
        parts.append(f"🚪 {l.room}")

    return "\n".join(parts)


def find_group_schedule(group_name):
    lessons = get_schedule_by_group(group_name)

    if not lessons:
        return (
            f"Расписание для группы {group_name} не найдено.\n\n"
            "Проверь название группы — например: АСУб-25-1"
        )

    by_date = {}
    for l in lessons:
        by_date.setdefault(l.date, []).append(l)

    answer = f"📚 Расписание группы {group_name}\n"
    answer += f"Всего дней: {len(by_date)}\n\n"

    sorted_dates = sorted(by_date.keys(), key=parse_date)

    for date in sorted_dates[:3]:
        answer += f"━━━ {format_date_display(date)} ━━━\n"
        day_lessons = deduplicate(by_date[date])
        day_lessons.sort(key=lambda l: sort_time(l.time_start))
        for l in day_lessons:
            answer += format_lesson(l) + "\n\n"

    if len(by_date) > 3:
        answer += f"... ещё {len(by_date) - 3} дней\n"
        answer += "Для просмотра конкретного дня напиши дату: 01.04.2026"

    return answer


def find_teacher_schedule(teacher):
    lessons = get_schedule_by_teacher(teacher)

    if not lessons:
        return (
            f"Преподаватель '{teacher}' не найден.\n\n"
            "Попробуй написать только фамилию, например: преподаватель Павлова"
        )

    by_date = {}
    for l in lessons:
        by_date.setdefault(l.date, []).append(l)

    answer = f"👨‍🏫 Расписание: {teacher}\n\n"

    for date in sorted(by_date.keys(), key=parse_date)[:3]:
        answer += f"━━━ {format_date_display(date)} ━━━\n"
        day_lessons = deduplicate(by_date[date])
        day_lessons.sort(key=lambda l: sort_time(l.time_start))
        for l in day_lessons:
            answer += format_lesson(l, show_group=True) + "\n\n"

    if len(by_date) > 3:
        answer += f"... ещё {len(by_date) - 3} дней"

    return answer


def find_date_schedule(date):
    lessons = get_schedule_by_date(date)

    if not lessons:
        return (
            f"На {format_date_display(date)} занятий не найдено.\n\n"
            "Возможно, это выходной или дата вне текущего месяца."
        )

    unique = deduplicate(lessons)
    unique.sort(key=lambda l: sort_time(l.time_start))

    answer = f"📅 Расписание на {format_date_display(date)}\n\n"
    for l in unique:
        answer += format_lesson(l) + "\n\n"

    return answer.strip()


def find_group_day_schedule(group_name: str, date: str):
    """Расписание конкретной группы на конкретный день"""
    lessons = get_schedule_by_group_and_date(group_name, date)

    if not lessons:
        return (
            f"На {format_date_display(date)} у группы {group_name} занятий нет.\n\n"
            "Возможно, это выходной или дата вне текущего месяца."
        )

    unique = deduplicate(lessons)
    unique.sort(key=lambda l: sort_time(l.time_start))

    answer = f"📅 Расписание группы {group_name} на {format_date_display(date)}\n\n"
    for l in unique:
        answer += format_lesson(l) + "\n\n"

    return answer.strip()