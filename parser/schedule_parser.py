import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import re
import requests
from bs4 import BeautifulSoup

from config.parser_config import DEFAULT_MONTH, DEFAULT_YEAR


def get_month_dates(group_id, month=DEFAULT_MONTH, year=DEFAULT_YEAR):
    """Получаем список дат и ссылок на расписание группы за месяц"""

    url = "https://www.istu.edu/Sys/Module/ScheduleClassList/v2/calendar.ajax.php"

    data = {
        "params": f'{{"month":{month},"year":{year},"group_id":"{group_id}"}}'
    }

    headers = {"X-Requested-With": "XMLHttpRequest"}

    response = requests.post(url, data=data, headers=headers)
    result = response.json()

    return result["dates"]


def get_lessons_for_day(day_url, target_date=None):
    """
    Парсим страницу недели, берём занятия только для target_date.
    target_date — строка вида '2026-04-01' (из API календаря).

    Структура сайта:
    - Страница показывает НЕДЕЛЮ (5 дней)
    - Каждый день: <div class="sch-list-day" data-params="{'date':'01.04.2026'}">
    - Внутри дня: <div class="sch-list-item"> — временные слоты
    - Дата берётся из data-params атрибута
    - Тип занятия: <div class="schcls-item-distype type-1"> (лекция/практика/лаб)
    """

    response = requests.get(day_url)
    soup = BeautifulSoup(response.text, "html.parser")

    lessons = []
    seen = set()

    # Словарь типов занятий по классу CSS
    LESSON_TYPES = {
        "type-1": "лекция",
        "type-2": "практика",
        "type-3": "лабораторная",
        "type-4": "семинар",
        "type-5": "экзамен",
        "type-6": "зачёт",
        "type-7": "консультация",
    }

    day_blocks = soup.find_all("div", class_="sch-list-day")

    if not day_blocks:
        day_blocks = [soup]

    for day_block in day_blocks:

        # Фильтруем по дате через data-params
        if target_date and day_blocks[0] is not soup:
            data_params = day_block.get("data-params", "")
            date_match = re.search(r"'date'\s*:\s*'([^']+)'", data_params)
            block_date = date_match.group(1) if date_match else ""

            try:
                from datetime import datetime
                dt = datetime.strptime(target_date, "%Y-%m-%d")
                target_date_formatted = dt.strftime("%d.%m.%Y")
            except Exception:
                target_date_formatted = target_date

            if block_date != target_date_formatted:
                continue

        schedule_items = day_block.find_all("div", class_="sch-list-item")

        for item in schedule_items:

            time_block = item.find("div", class_="sch-list-item-time-inner")
            lesson_time = time_block.text.strip() if time_block else ""

            lesson_cards = item.find_all("div", class_="schcls-item schcls-card")

            for card in lesson_cards:

                card_classes = card.get("class", [])
                if "schcls-card-other" in card_classes:
                    continue

                style = card.get("style", "")
                if "opacity" in style:
                    continue

                subject_block = card.find("div", class_="schcls-item-name")
                teacher_block = card.find("div", class_="schcls-item-prepod")
                room_block = card.find("div", class_="schcls-item-aud")

                subject = subject_block.text.strip() if subject_block else ""
                teacher = teacher_block.text.strip() if teacher_block else ""
                room = room_block.text.strip() if room_block else ""

                if not subject or subject.lower() == "свободно":
                    continue

                # Определяем тип занятия по CSS классу
                lesson_type = ""
                distype_block = card.find("div", class_="schcls-item-distype")
                if distype_block:
                    distype_classes = distype_block.get("class", [])
                    for cls in distype_classes:
                        if cls in LESSON_TYPES:
                            lesson_type = LESSON_TYPES[cls]
                            break
                    # Если тип не в словаре — берём текст напрямую
                    if not lesson_type:
                        lesson_type = distype_block.text.strip()

                # Подгруппа
                subgroup = ""
                group_blocks = card.find_all("div", class_="schcls-item-group")
                for gb in group_blocks:
                    gb_text = gb.text.strip()
                    if "подгруппа" in gb_text.lower():
                        subgroup_parts = gb_text.split("подгруппа")
                        if len(subgroup_parts) > 1:
                            subgroup = "подгруппа " + subgroup_parts[1].strip()
                        break

                key = (lesson_time, subject, teacher)
                if key in seen:
                    continue
                seen.add(key)

                lessons.append({
                    "time": lesson_time,
                    "subject": subject,
                    "teacher": teacher,
                    "room": room,
                    "subgroup": subgroup,
                    "lesson_type": lesson_type
                })

    return lessons