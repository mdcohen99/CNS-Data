from __future__ import annotations

import sys
from datetime import date, datetime
from typing import Iterable, Set

import pandas as pd
import requests


EVENT_DATES_ENDPOINT = "https://www.bccenter.org/services/eventsservice.asmx/GetEventDays"


def fetch_event_dates(year: int) -> Set[date]:
    """Return the set of individual event dates hosted during *year*."""

    payload = {
        "day": "",
        "startDate": f"01/01/{year}",
        "endDate": f"12/31/{year}",
        "categoryID": 0,
        "currentUserItems": "false",
        "tagID": 0,
        "keywords": "",
        "isFeatured": "false",
        "fanPicks": "false",
        "myPicks": "false",
        "pastEvents": "true",
        "allEvents": "true",
        "memberEvents": "false",
        "memberOnly": "false",
        "showCategoryExceptionID": 0,
        "isolatedSchedule": 0,
        "customFieldFilters": [],
        "searchInDescription": False,
    }

    response = requests.post(EVENT_DATES_ENDPOINT, json=payload, timeout=60)
    response.raise_for_status()

    raw_dates = response.json().get("d", [])
    event_dates: Set[date] = set()

    for token in raw_dates:
        if not isinstance(token, str):
            continue
        if token.startswith("month "):
            continue
        try:
            parsed = datetime.strptime(token, "%m/%d/%Y").date()
        except ValueError:
            continue
        if parsed.year == year:
            event_dates.add(parsed)

    return event_dates


def build_calendar(year: int, occupied_days: Iterable[date]) -> pd.DataFrame:
    """Construct a daily occupancy calendar for *year*."""

    day_set = set(occupied_days)
    calendar = pd.DataFrame({
        "date": pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D"),
    })
    calendar["Baltimore Convention Center"] = calendar["date"].dt.date.apply(
        lambda current: int(current in day_set)
    )
    return calendar


def main(year: int = 2024) -> None:
    event_dates = fetch_event_dates(year)
    print(f"Fetched {len(event_dates)} event days for {year}.")

    if not event_dates:
        print("No events returned for the requested year.")
        return

    calendar = build_calendar(year, event_dates)
    print(calendar.head(20))

    output_path = f"bcc_events_calendar_{year}.csv"
    calendar.to_csv(output_path, index=False)
    print(f"Saved daily calendar to {output_path}")


if __name__ == "__main__":
    selected_year = 2024
    if len(sys.argv) > 1:
        try:
            selected_year = int(sys.argv[1])
        except ValueError:
            raise SystemExit("Year argument must be an integer, e.g. 2024")

    main(selected_year)