"""
source for activity watch

Uses aw-client (https://github.com/ActivityWatch/aw-client)

Heavily inspired by this example: https://github.com/ActivityWatch/aw-client/blob/master/examples/working_hours.py
"""

from dataclasses import asdict, dataclass
import json
import logging
import os
import socket
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional, Tuple

import aw_client
from aw_client import queries
from aw_core import Event
from aw_transform import flood

from database import Database
from fetch import Source


OUTPUT_HTML = os.environ.get("OUTPUT_HTML", "").lower() == "true"

td1d = timedelta(days=1)
day_offset = timedelta(hours=4)

# NOTE: we ignore case for all
CATEGORY_REGEXES = {
    "ata": r"\bata\b|PowerShell|documentation|code",
    "school": r"\b[a-zA-Z]{2,4}\d{2,4}\b|data-aggregator|PowerShell|Pset|problem set|documentation|Lecture|code",  # match on course codes with 2-4 letters, then 2-4 digits
    "tv": r"netflix|crunchyroll",
    "research": r"arxiv|diffusion|flow matching",
    "youtube": r"youtube",
    "languages": r"lingq",
    "reading": r"instapaper|crafting interpreters",
}


@dataclass
class JoinedEvent:
    timestamp: datetime
    duration: timedelta
    category: str


def join_close_events(events: List[dict], max_break: float) -> List[JoinedEvent]:
    """
    Joins events together if they're separated by at most max_break

    max_break: Max time (in seconds) to flood when there's an empty slot between events
    """

    events_e: List[Event] = [Event(**e) for e in events]
    events_e = flood(events_e, max_break)

    joined_events = []
    events_to_join = []
    prev_end: datetime = None
    for event in events_e:
        if len(events_to_join) == 0 or prev_end == event["timestamp"]:
            events_to_join.append(event)
        else:
            # merge events and add to joined_events
            joined_events.append(
                JoinedEvent(
                    timestamp=events_to_join[0]["timestamp"],
                    duration=sum(
                        map(lambda e: e["duration"], events_to_join), timedelta()
                    ),
                    category=events_to_join[0]["data"]["$category"][0],
                )
            )

            # get ready for next super event
            events_to_join = []
        prev_end = event["timestamp"] + event["duration"]

    return joined_events


def query(timeperiods: List[List[date]], hostname: str):
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


class ComputerUseSource(Source):
    id = "computer_use"
    schema = ["timestamp timestamp", "duration timedelta", "category TEXT"]

    @classmethod
    def fetch(cls, last_queried: Optional[datetime]) -> List[Dict]:
        """
        Fetch from last fetched timestamp until now, flood events up to max_break, and insert into database
        """
        hostname = socket.gethostname()

        if last_queried is not None:
            fetch_start = last_queried
        else:
            fetch_start = (
                datetime.combine(date(2020, 7, 15), time()) + day_offset
            ).astimezone()
        fetch_end = datetime.now().astimezone()

        # fetch raw events from API and classify with regex
        raw_events = query([[fetch_start, fetch_end]], hostname)[0]["events"]

        # flood to join close segments for each category
        joined_events: List[JoinedEvent] = []
        for category in CATEGORY_REGEXES.keys():
            category_events = [
                e for e in raw_events if category in e["data"]["$category"]
            ]
            res = join_close_events(category_events, max_break=300)
            joined_events.extend(res)

        return [asdict(je) for je in joined_events]
