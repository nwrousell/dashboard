from datetime import datetime, timedelta


def get_start_of_week(dt: datetime = None) -> datetime:
    """
    Returns the datetime at the beginning of the week (Monday at 00:00) for the given datetime.
    If no datetime is provided, uses the current datetime.
    """
    if dt is None:
        dt = datetime.now()
    start_of_week = dt - timedelta(days=dt.weekday())
    return datetime.combine(start_of_week.date(), datetime.min.time())


def get_timeperiods(
    start: datetime, delta: timedelta, count: int
) -> list[tuple[datetime, datetime]]:
    """
    Generates a list of (start, end) datetime tuples.
    Each period is of duration `delta`, starting from `start`, for a total of `count` periods.
    """
    periods = []
    for i in range(count):
        period_start = start + i * delta
        period_end = period_start + delta
        periods.append((period_start, period_end))
    return periods
