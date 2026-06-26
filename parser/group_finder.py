import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ru-RU,ru;q=0.9',
}


def get_groups(department_id):
    url = f"https://www.istu.edu/raspisanie/podrazdelenie/{department_id}"
    response = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    result = {}
    groups = soup.find_all("div", class_="schd-grp-item")

    for group in groups:
        link = group.find("a")
        if not link:
            continue
        group_name = link.text.strip()
        href = link["href"]
        group_id = href.split("/")[-1]
        result[group_name] = group_id

    return result


def find_group_id(group_name, department_id=683, groups_cache=None):
    """
    groups_cache — уже загруженный словарь групп.
    Если передан — не делаем лишний запрос к сайту.
    """
    if groups_cache is not None:
        return groups_cache.get(group_name)

    groups = get_groups(department_id)
    return groups.get(group_name)