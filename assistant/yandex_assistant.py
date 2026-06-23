import re

from assistant.knowledge_base import (
    find_group_schedule,
    find_teacher_schedule,
    find_date_schedule
)


def process_message(text: str):

    text_clean = text.lower()

    # --- ГРУППА ---
    group = re.search(r"[А-Яа-я]+-\d{2}-\d", text)

    if group:
        return find_group_schedule(group.group())

    # --- ПРЕПОД ---
    if "преподаватель" in text_clean:
        words = text.split()

        for w in words:
            if w.istitle():
                return find_teacher_schedule(w)

    # --- ДАТА ---
    date = re.search(r"\d{2}\.\d{2}\.\d{4}", text)

    if date:
        return find_date_schedule(date.group())

    return "Не понял запрос 😕"