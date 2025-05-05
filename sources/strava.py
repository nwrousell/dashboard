"""
strava source
"""

from typing import Dict, List, Optional
from datetime import datetime

from fetch import Source


class StravaSource(Source):
    id = "strava"
    schema = [
        "timestamp timestamp",
        "duration timedelta",
        "name TEXT",
        "description TEXT",
        "distance_mi FLOAT",
    ]

    @classmethod
    def fetch(cls, last_queried: Optional[datetime]) -> List[Dict]:
        pass


# StravaSource.register()
