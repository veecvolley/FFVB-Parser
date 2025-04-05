import requests
from bs4 import BeautifulSoup

URL = "https://www.ffvbbeach.org/ffvbapp/resu/planning_club.php?aff_semaine=PRE&date_jour=1742598000&cnclub=0775819&x=1&y=9"
page = requests.get(URL)

print(page.text)

soup = BeautifulSoup(page.content, "html.parser")


