"""Generate obviously synthetic CLI fixtures. Never historical performance."""

import csv
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


def main():
    out = Path("eaa/fixtures")
    out.mkdir(parents=True, exist_ok=True)
    day, zone, days, trades, paths = date(2026, 1, 5), ZoneInfo("America/New_York"), [], [], []
    while len(days) < 40:
        if day.weekday() < 5:
            i = len(days)
            days.append([str(day)])
            if i % 7 != 0:
                ident = f"SYNTHETIC-{i:03}"
                entry = datetime.combine(day, datetime.min.time().replace(hour=10), zone)
                points = -25 if i % 4 == 0 else 40
                trades.append([ident, entry.isoformat(), (entry + timedelta(minutes=5)).isoformat(), "long", 20000, 20000 + points, 1, 25])
                for minute, p in ((1, -20), (2, points / 2), (4, points)):
                    paths.append([ident, (entry + timedelta(minutes=minute)).isoformat(), p])
        day += timedelta(days=1)
    for name, header, rows in [
        ("synthetic_calendar.csv", ["session_date"], days),
        ("synthetic_trades.csv", ["trade_id", "entry_time", "exit_time", "side", "entry_price", "exit_price", "contracts", "stop_points"], trades),
        ("synthetic_paths.csv", ["trade_id", "time", "unrealized_points"], paths),
    ]:
        with (out / name).open("w", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(header)
            writer.writerows(rows)
    print("SYNTHETIC ONLY: generated 40 session fixtures")


if __name__ == "__main__":
    main()
