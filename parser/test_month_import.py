import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import requests


def get_month_dates():

    url = "https://www.istu.edu/Sys/Module/ScheduleClassList/v2/calendar.ajax.php"

    data = {
        "params": '{"month":4,"year":2026,"group_id":"473841"}'
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


dates = get_month_dates()

for date, info in dates.items():

    full_url = "https://www.istu.edu" + info["link"]

    response = requests.get(full_url)

    print(
        date,
        response.status_code
    )