"""
proof of concept simple weekly time stacked bar chart
"""

from termcolor import colored
import json
from datetime import datetime, time, timedelta

from typing import List

MINUTES_TO_CHAR = 15

td1d = timedelta(days=1)
day_offset = timedelta(hours=4)

CATEGORY_COLORS = {
    "ATA": "green",
    "Reading": "yellow",
    "Entertainment": "light_magenta",
    "School": "blue",
    "Languages": "red",
}

DAYS_OF_WEEK = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def print_stacked_bar(day, category_to_values):
    bar = ""
    values = ""

    total = 0

    for category, value in category_to_values.items():
        if value > 0:
            chars = round(value / MINUTES_TO_CHAR)
            bar += colored("█" * chars, CATEGORY_COLORS[category])
            hours = round(value / 60, ndigits=1)
            values += colored(f"{hours}h", CATEGORY_COLORS[category]) + " "
            total += value

    values += str(round(total / 60, ndigits=1))

    print(f"{day}: {bar}| {values}")


def print_key():
    print("KEY:")
    key = ""
    for category, color in CATEGORY_COLORS.items():
        key += colored(category, color) + " "
    key += "Total"
    print(key)


def last_seven_days() -> List[datetime]:
    now = datetime.now().astimezone()
    today = (datetime.combine(now.date(), time()) + day_offset).astimezone()
    days = [today - i * td1d for i in range(7)]
    days.reverse()
    return days


def main():
    print()

    with open("../sources/out2.json", "rt") as f:
        data = json.load(f)

    days = last_seven_days()
    for day in days:
        day_durations = filter(lambda e: e["day"] == day.isoformat(), data)
        day_str = (
            f"{DAYS_OF_WEEK[day.weekday()][:3]} ({day.month}/{day.day}/{day.year})"
        )
        category_to_values = {
            e["category"]: round(e["duration_seconds"] / 60) for e in day_durations
        }
        print_stacked_bar(day_str, category_to_values)

    print()
    print_key()
    print()


if __name__ == "__main__":
    main()
