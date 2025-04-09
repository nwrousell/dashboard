"""
source for activity watch

Uses aw-client (https://github.com/ActivityWatch/aw-client)

Heavily inspired by this example: https://github.com/ActivityWatch/aw-client/blob/master/examples/working_hours.py
"""

import json
import logging
import os
import socket
from datetime import datetime, time, timedelta
from typing import Dict, List, Tuple

import aw_client
from aw_client import queries
from aw_core import Event
from aw_transform import flood


OUTPUT_HTML = os.environ.get("OUTPUT_HTML", "").lower() == "true"

td1d = timedelta(days=1)
day_offset = timedelta(hours=4)

# NOTE: we ignore case for all
CATEGORY_REGEXES = {
    "ATA": r"\bata\b",
    "School": r"\b[a-zA-Z]{2,4}\d{2,4}\b",  # match on course codes with 2-4 letters, then 2-4 digits
    "Entertainment": r"netflix|youtube",
    "Languages": r"lingq",
    "Reading": r"instapaper|crafting interpreters",
}


def generous_approx(events: List[dict], category: str, max_break: float) -> timedelta:
    """
    Returns a generous approximation of time on category by including non-categorized time when shorter than a specific duration

    max_break: Max time (in seconds) to flood when there's an empty slot between events
    """
    events_e: List[Event] = [
        Event(**e) for e in events if category in e["data"]["$category"]
    ]
    return sum(
        map(lambda e: e.duration, flood(events_e, max_break)),
        timedelta(),
    )


def query(timeperiods, hostname: str):
    categories: List[Tuple[List[str], Dict]] = [
        (
            [category],
            {
                "type": "regex",
                "regex": regex,
                "ignore_case": True,
            },
        )
        for category, regex in CATEGORY_REGEXES.items()
    ]

    aw = aw_client.ActivityWatchClient(client_name="data_aggregator")

    canonicalQuery = queries.canonicalEvents(
        queries.DesktopQueryParams(
            bid_window=f"aw-watcher-window_{hostname}",
            bid_afk=f"aw-watcher-afk_{hostname}",
            classes=categories,
            filter_classes=[[cat] for cat in CATEGORY_REGEXES.keys()],
        )
    )
    query = f"""
    {canonicalQuery}
    duration = sum_durations(events);
    RETURN = {{"events": events, "duration": duration}};
    """

    res = aw.query(query, timeperiods)

    return res


def aw_fetch_last_week():
    hostname = socket.gethostname()

    now = datetime.now().astimezone()
    today = (datetime.combine(now.date(), time()) + day_offset).astimezone()

    timeperiods = [(today - i * td1d, today - (i - 1) * td1d) for i in range(7)]
    timeperiods.reverse()

    raw_queries = query(timeperiods, hostname)  # one obj per day containing all events

    category_durations = []
    for day_queries, day_timeperiod in zip(raw_queries, timeperiods):
        events = day_queries["events"]
        for category in CATEGORY_REGEXES.keys():
            duration: timedelta = generous_approx(events, category, max_break=180)
            category_durations.append(
                {
                    "category": category,
                    "duration_seconds": duration.total_seconds(),
                    "day": day_timeperiod[0].isoformat(),
                }
            )

    with open("out2.json", "wt") as f:
        json.dump(category_durations, f)


if __name__ == "__main__":
    # ignore log warnings in aw_transform
    logging.getLogger("aw_transform").setLevel(logging.ERROR)

    aw_fetch_last_week()
