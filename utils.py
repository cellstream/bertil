import datetime
import json
import requests
from html.parser import HTMLParser

def fetch_food_json():
    response = requests.get('http://www.hanssonohammar.se/veckansmeny.json').text
    return json.loads(response)


def get_food_from_json(data, restaurant, day):
    if day not in data:
        return "(no mat " + str(day) + ")"

    if restaurant == 'IKSU':
        mat_today = data[day][0]
    elif restaurant == 'KONST':
        mat_today = data[day][1]
    else:
        return "(restaurant not known)"

    if restaurant not in mat_today:
        return "(no {} today)".format(restaurant)

    return "\n".join(mat_today[restaurant])


def get_food(restaurant, day):
    # Get JSON
    data = fetch_food_json()
    return get_food_from_json(data, restaurant, day)


# Takes a year, returns a year worth of json from api.dryg.net
# See https://api.dryg.net/ for json format
def get_swedish_year(year):
    return requests.get('https://api.dryg.net/dagar/v2.1/{year}'.format(
        year=year)).json()


# Takes a year and a month, returns a month worth of json from api.dryg.net
def get_swedish_month(year, month):
    return requests.get('https://api.dryg.net/dagar/v2.1/{year}/{month}'.format(
        year=year, month=month)).json()


# Takes a year, a month and a day, returns an array containing a weeks
# worth of json aquired from api.dryg.net representing the week in which
# the date sent to function resides
def get_swedish_week(year, month, day):
    month_json = get_swedish_month(year, month)['dagar']
    month_before_json = None
    month_after_json = None

    date = datetime.date(year, month, day)

    if month == 1:
        month_before_json = get_swedish_month(year - 1, 12)['dagar']
        month_after_json = get_swedish_month(year, month + 1)['dagar']
    elif month == 12:
        month_before_json = get_swedish_month(year, month - 1)['dagar']
        month_after_json = get_swedish_month(year + 1, 1)['dagar']
    else:
        month_before_json = get_swedish_month(year, month - 1)['dagar']
        month_after_json = get_swedish_month(year, month + 1)['dagar']

    today_index = len(month_before_json) + date.day - 1
    monday_index = today_index - date.weekday()
    sunday_index = today_index + (7 - date.weekday())

    all_days = sum([month_before_json, month_json, month_after_json], [])

    return all_days[monday_index:sunday_index]


# Returns an array containing the current week in json from api.dryg.net
def get_current_swedish_week():
    today = datetime.datetime.today()
    return get_swedish_week(today.year, today.month, today.day)


# Takes a year, month and day, returns the json string representing
# this day aquired from api.dryg.net
def get_swedish_day(year, month, day):
    return requests.get('https://api.dryg.net/dagar/v2.1/{year}/{month}/{day}'.format(
        year=year, month=month, day=day)).json()


# Takes an array with a weeks worth of json from api.dryg.net along
# with a weekday index. Makes a shitty guess and returns True if the
# day is a squeeze day, False otherwise, _highly_ unreliable
def is_squeeze_day(weekday_index, week_json):
    day_before = weekday_index - 1 if weekday_index > 0 else weekday_index
    day_after = weekday_index + 1 if weekday_index < 6 else weekday_index

    return (week_json[day_before]['röd dag'] == 'Ja' or
            week_json[day_after]['röd dag'] == 'Ja')


# Takes a day json string from api.dryg.net
# Returns True if day is Workfree, False otherwise
def is_workfree_day(day):
    return day['arbetsfri dag'] == 'Ja'

def majestic():
    class Parser(HTMLParser):

        def __init__(self):
            super().__init__()
            self.current_tag = []
            self.result = []

        def handle_starttag(self, tag, attrs):
            self.current_tag.append((tag, attrs))

        def handle_endtag(self, tag):
            self.current_tag.pop()

        def handle_data(self, data):
            if self.current_tag:
                tag, attrs = self.current_tag[-1]
                if tag == 'div':
                    for k, v in attrs:
                        if k == 'class' and v == 'menu':
                            tmp = data.strip()
                            if tmp:
                                self.result.append(tmp)

    r = requests.get('http://mega.vk.se/lunchguiden/?view=restaurant&id=204')
    r.encoding = "UTF-8"
    p = Parser()
    p.feed(r.text)
    return p.result
