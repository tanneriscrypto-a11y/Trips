#!/usr/bin/env python3
"""Wait times for WDW / Universal Orlando parks.

Usage:
  waits.py live <park>          Print current wait times (Queue-Times)
  waits.py hours <park> [date]  Park hours/schedule (ThemeParks.wiki, date YYYY-MM-DD)
  waits.py crowdcal <park> [YYYY[-MM]]  Historical daily avg wait, 2014-present (Thrill Data)
  waits.py log [--out DIR] [parks...]   Append a snapshot of all (or named) parks to CSV
  waits.py parks                List known park slugs

Wait time data powered by Queue-Times.com (https://queue-times.com) and
Thrill Data (https://www.thrill-data.com).
"""
import csv
import datetime
import json
import pathlib
import sys
import urllib.request

QT = {
    "magic-kingdom": 6,
    "epcot": 5,
    "hollywood-studios": 7,
    "animal-kingdom": 8,
    "universal-studios": 65,
    "islands-of-adventure": 64,
    "epic-universe": 334,
    "volcano-bay": 67,
}

TPW = {
    "magic-kingdom": "75ea578a-adc8-4116-a54d-dccb60765ef9",
    "epcot": "47f90d2c-e191-4239-a466-5892ef59a88b",
    "hollywood-studios": "288747d1-8b4f-4a64-867e-ea7c9b27bad8",
    "animal-kingdom": "1c84a229-8862-4648-9c71-378ddd2c7693",
    "typhoon-lagoon": "b070cbc5-feaa-4b87-a8c1-f94cca037a18",
    "blizzard-beach": "ead53ea5-22e5-4095-9a83-8c29300d7c63",
    "universal-studios": "eb3f4560-2383-4a36-9152-6b3e5ed6bc57",
    "islands-of-adventure": "267615cc-8943-4c2a-ae2c-5da728ca591f",
    "epic-universe": "12dbb85b-265f-44e6-bccf-f1faa17211fc",
    "volcano-bay": "fe78a026-b91b-470c-b906-9d2266b692da",
}

# Thrill Data crowd-calendar slugs (https://www.thrill-data.com/wa/park-crowdcal/<slug>)
THRILL = {
    "magic-kingdom": "magic-kingdom",
    "epcot": "epcot",
    "hollywood-studios": "hollywood-studios",
    "animal-kingdom": "animal-kingdom",
    "universal-studios": "universal-studios",
    "islands-of-adventure": "islands-of-adventure",
    "epic-universe": "epic-universe",
    "volcano-bay": "volcano-bay",
}

DEFAULT_OUT = pathlib.Path(__file__).resolve().parents[4] / "Disney Universal" / "data"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Trips-planner/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def qt_rides(slug):
    data = get(f"https://queue-times.com/parks/{QT[slug]}/queue_times.json")
    rides = list(data.get("rides", []))
    for land in data.get("lands", []):
        for ride in land["rides"]:
            ride["land"] = land["name"]
            rides.append(ride)
    return rides


def cmd_live(slug):
    rides = sorted(qt_rides(slug), key=lambda r: -r["wait_time"])
    print(f"{slug} — {len(rides)} rides — {datetime.datetime.now():%Y-%m-%d %H:%M}")
    for r in rides:
        status = f"{r['wait_time']:>4} min" if r["is_open"] else "  CLOSED"
        print(f"{status}  {r['name']}  [{r.get('land', '-')}]")
    print("\nPowered by Queue-Times.com")


def cmd_hours(slug, date=None):
    sched = get(f"https://api.themeparks.wiki/v1/entity/{TPW[slug]}/schedule")
    for day in sched.get("schedule", []):
        if date and day["date"] != date:
            continue
        print(f"{day['date']}  {day['type']:<16} {day.get('openingTime','')} - {day.get('closingTime','')}")


def cmd_crowdcal(slug, when=None):
    data = get(f"https://www.thrill-data.com/wa/park-crowdcal/{THRILL[slug]}")
    points = [p for p in data["points"] if not when or p["date"].startswith(when)]
    if not points:
        print(f"no data for {slug} {when or ''}")
        return
    waits = [p["wait"] for p in points]
    print(f"{slug} — {points[0]['date']} .. {points[-1]['date']} — {len(points)} days")
    print(f"avg {sum(waits) / len(waits):.1f} min, min {min(waits):.0f}, max {max(waits):.0f}")
    for p in points[-60:] if not when else points:
        bar = "#" * int(p["wait"] // 2)
        print(f"{p['date']}  {p['wait']:>5.0f}  {bar}")
    print("\nData: Thrill Data (thrill-data.com)")


def cmd_log(args):
    out = DEFAULT_OUT
    if "--out" in args:
        i = args.index("--out")
        out = pathlib.Path(args[i + 1])
        del args[i:i + 2]
    slugs = args or list(QT)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "wait_times.csv"
    new = not path.exists()
    now = datetime.datetime.now().isoformat(timespec="minutes")
    with path.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "park", "land", "ride", "is_open", "wait_min"])
        for slug in slugs:
            try:
                for r in qt_rides(slug):
                    w.writerow([now, slug, r.get("land", ""), r["name"], r["is_open"], r["wait_time"]])
            except Exception as e:
                print(f"warn: {slug}: {e}", file=sys.stderr)
    print(f"logged {slugs} -> {path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "live" and args:
        cmd_live(args[0])
    elif cmd == "hours" and args:
        cmd_hours(*args[:2])
    elif cmd == "crowdcal" and args:
        cmd_crowdcal(*args[:2])
    elif cmd == "log":
        cmd_log(args)
    elif cmd == "parks":
        print("\n".join(sorted(set(QT) | set(TPW))))
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
