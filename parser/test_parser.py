import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from parser.schedule_parser import (
    get_month_dates,
    get_lessons_for_day
)

dates = get_month_dates()

first_date = list(dates.keys())[0]

first_link = dates[first_date]["link"]

full_url = "https://www.istu.edu" + first_link

lessons = get_lessons_for_day(full_url)

print("Дата:", first_date)
print("Занятий:", len(lessons))

for lesson in lessons[:5]:
    print(lesson)