import requests
from bs4 import BeautifulSoup


def get_groups(department_id):

    url = f"https://www.istu.edu/raspisanie/podrazdelenie/{department_id}"

    response = requests.get(url)

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    result = {}

    groups = soup.find_all(
        "div",
        class_="schd-grp-item"
    )

    for group in groups:

        link = group.find("a")

        if not link:
            continue

        group_name = link.text.strip()

        href = link["href"]

        group_id = href.split("/")[-1]

        result[group_name] = group_id

    return result


def find_group_id(
    group_name,
    department_id=683
):

    groups = get_groups(department_id)

    return groups.get(group_name)
