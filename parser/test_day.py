import requests

url = "https://www.istu.edu/raspisanie/grup/473841/07.04.2026/"

response = requests.get(url)

html = response.text

print("Менеджмент найден:", "Менеджмент" in html)
print("Наумова найдена:", "Наумова" in html)
print("Онлайн найден:", "Онлайн" in html)