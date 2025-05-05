"""
source for Hevy


they have a public API (https://api.hevyapp.com/docs/#/Workouts/get_v1_workouts), but you need to pay for pro for it.

Pro isn't that expensive and I like Hevy, so not the biggest deal. But their internal API works from Postman, so unless they refresh the auth
token often, I can use that. (they probably refresh the auth-token)
"""

from typing import Dict, List, Optional
from datetime import datetime
import requests

from fetch import Source

USERNAME = "nwrousell"

HEADERS = {
    "X-Api-Key": "shelobs_hevy_web",
    "Host": "api.hevyapp.com",
    "Auth-Token": "63473cdb-0d0f-4f31-bade-b496091bb7b4",
}


class HevySource(Source):
    id = "hevy_summary"
    schema = [
        "timestamp timestamp",
        "duration timedelta",
        "name TEXT",
        "description TEXT",
        "volume_lb FLOAT",
    ]

    @classmethod
    def fetch(cls, last_queried: Optional[datetime]) -> List[Dict]:
        offset = 0
        rows: List[Dict] = []
        while True:
            workout_res = cls._fetch_workouts(offset=offset)
            if workout_res is None:
                raise Exception("request failed")

            if len(workout_res["workouts"]) == 0:
                break

            for workout in workout_res["workouts"]:
                workout_date = datetime.fromtimestamp(workout["end_time"])
                if last_queried is not None and workout_date < last_queried:
                    return rows

                rows.append(cls._workout_res_to_row(workout))
                print(rows[-1])
                offset += 1

        return rows

    @classmethod
    def _workout_res_to_row(cls, workout_res: Dict) -> Dict:
        "Convert the json dict returned by the user_workouts endpoint for a workout to the associated rows to store"

        ts = datetime.fromtimestamp(workout_res["start_time"])
        return {
            "timestamp": ts,
            "duration": datetime.fromtimestamp(workout_res["end_time"]) - ts,
            "name": workout_res["name"],
            "description": workout_res["description"],
            "volume_lb": workout_res["estimated_volume_kg"],
        }

    @classmethod
    def _get_hevy_endpoint(cls, username: str, limit: int, offset: int):
        return f"https://api.hevyapp.com/user_workouts_paged?username={username}&limit={limit}&offset={offset}"

    @classmethod
    def _fetch_workouts(cls, limit: int = 5, offset: int = 0) -> Dict:
        assert limit <= 5 and "api dictates limit <= 5"
        endpoint = cls._get_hevy_endpoint(username=USERNAME, limit=limit, offset=offset)
        res = requests.get(
            endpoint,
            headers=HEADERS,
        )
        if res.status_code == 200:
            return res.json()
        else:
            print(
                f"request to {endpoint} failed with status code {res.status_code}: {res.reason}"
            )
            return None


HevySource.register()

if __name__ == "__main__":
    HevySource.fetch(None)
