import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import requests
from bs4 import BeautifulSoup

from config.parser_config import (
    GROUP_ID,
    DEFAULT_MONTH,
    DEFAULT_YEAR
)


def get_month_dates(
    group_id,
    month=DEFAULT_MONTH,
    year=DEFAULT_YEAR
):

    url = "https://www.istu.edu/Sys/Module/ScheduleClassList/v2/calendar.ajax.php"

    data = {
        "params": f'{{"month":{month},"year":{year},"group_id":"{group_id}"}}'
    }

    headers = {
        "X-Requested-With": "XMLHttpRequest"
    }

    response = requests.post(
        url,
        data=data,
        headers=headers
    )

    result = response.json()

    return result["dates"]


def get_lessons_for_day(day_url):

    response = requests.get(day_url)
    soup = BeautifulSoup(response.text, "html.parser")

    lessons = []
    seen = set()

    schedule_items = soup.find_all("div", class_="sch-list-item")

    for item in schedule_items:

        time_block = item.find("div", class_="sch-list-item-time-inner")
        lesson_time = time_block.text.strip() if time_block else ""

        # ⚠️ ВАЖНО: берём ТОЛЬКО уникальные предметы внутри времени
        subjects_seen = set()

        lesson_cards = item.find_all("div", class_="schcls-item schcls-card")

        for card in lesson_cards:

            subject_block = card.find("div", class_="schcls-item-name")
            teacher_block = card.find("div", class_="schcls-item-prepod")
            room_block = card.find("div", class_="schcls-item-aud")

            subject = subject_block.text.strip() if subject_block else ""
            teacher = teacher_block.text.strip() if teacher_block else ""
            room = room_block.text.strip() if room_block else ""

            if not subject:
                continue

            # 🔥 ФИЛЬТР ПО ПРЕДМЕТУ ВНУТРИ ОДНОГО ВРЕМЕНИ
            if subject in subjects_seen:
                continue

            subjects_seen.add(subject)

            key = (lesson_time, subject)

            if key in seen:
                continue

            seen.add(key)

            lessons.append({
                "time": lesson_time,
                "subject": subject,
                "teacher": teacher,
                "room": room
            })

    return lessons