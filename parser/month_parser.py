import requests

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

print(result)