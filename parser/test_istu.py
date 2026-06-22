import requests
from bs4 import BeautifulSoup

url = "https://www.istu.edu/raspisanie/"

response = requests.get(url)

soup = BeautifulSoup(response.text, "html.parser")

form = soup.find("form")

print(form)