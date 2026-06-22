import requests
from bs4 import BeautifulSoup

url = "https://www.istu.edu/raspisanie/"

response = requests.get(url)

print(response.status_code)
print(response.url)