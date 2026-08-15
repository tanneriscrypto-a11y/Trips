#!/usr/bin/env python3
"""DVC availability watcher for the Jan 2027 Disney stay (Jan 26-30, AKV savanna hunt).

Polls the per-night availability API that dvcrentalstore.com's own frontend uses
(api.keyholdervacations.com, discovered 2026-08-14 — see planning/MASTER-PLAN.md)
for a small set of studio room types, diffs against saved state, and Pushover-alerts
only on improvements:

  Level 5  savanna studio (Jambo or Kidani), all 4 nights           -> CRITICAL
  Level 4  savanna nights across Jambo+Kidani cover all 4 nights    -> CRITICAL
  Level 3  savanna run of >=2 nights + one complement studio rest   -> alert
  Level 2  AKV standard/value studio, all 4 nights                  -> alert
  Level 1  some savanna night(s) open (no full assembly)            -> alert on newly
                                                                       opened nights only
Alerts are edge-triggered (level rises vs. previous run, or a savanna night flips
closed->open), so unchanged inventory never re-alerts. If savanna inventory vanishes
and later returns, that's a fresh transition and alerts again.

State in dvc_watcher_state.json; log in dvc_watcher.log; daily one-line summary
appended to dvc_inventory_log.md (all machine-local, gitignored).

Usage:
  dvc_watcher.py             one polling cycle (first run seeds state, no alerts)
  dvc_watcher.py --watch     poll forever every POLL_MINUTES (+jitter)
  dvc_watcher.py --dry       one cycle, print would-be alerts, send nothing
  dvc_watcher.py --status    show last-run summary from state and exit
  dvc_watcher.py --selftest  run the assembly solver against synthetic scenarios
  dvc_watcher.py --test      send a test Pushover notification and exit

Schedule on the always-on desktop ONLY (state/log belong to one machine):
  Task Scheduler: py.exe "C:\\...\\Disney Universal\\dvc_watcher.py", every 20 min
  (or run once with --watch inside a persistent session)
Be polite: ~9 tiny GETs per cycle, jittered, with 60-min backoff on 429/5xx.
"""
import json
import logging
import pathlib
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

HERE = pathlib.Path(__file__).resolve().parent
STATE_FILE = HERE / "dvc_watcher_state.json"
LOG_FILE = HERE / "dvc_watcher.log"
CREDS_FILE = HERE / "pushover_creds.json"
INVENTORY_LOG = HERE / "dvc_inventory_log.md"

# --- Trip config ---------------------------------------------------------
CHECK_IN = date(2027, 1, 26)
CHECK_OUT = date(2027, 1, 30)
NIGHTS = [(CHECK_IN + timedelta(days=i)).isoformat()
          for i in range((CHECK_OUT - CHECK_IN).days)]

# Rooms to watch. group: savanna = the target; akv_std = lodge-without-the-view
# fallback; complement = deluxe studio acceptable for the back half of a split
# (all better MK access, per daily_check.md judgment rules).
ROOMS = {
    "AKK-STU-SAV": {"label": "AKV Kidani Savanna Studio", "group": "savanna"},
    "AKV-STU-SAV": {"label": "AKV Jambo Savanna Studio", "group": "savanna"},
    "AKK-STU-STD": {"label": "AKV Kidani Standard Studio", "group": "akv_std"},
    "AKV-STU-STD": {"label": "AKV Jambo Standard Studio", "group": "akv_std"},
    "AKV-STU-VAL": {"label": "AKV Jambo Value Studio", "group": "akv_std"},
    "CCV-STU-STD": {"label": "Copper Creek Studio", "group": "complement"},
    "BRV-STU-STD": {"label": "Boulder Ridge Studio", "group": "complement"},
    "BLT-STU-STD": {"label": "Bay Lake Tower Studio", "group": "complement"},
    "POL-STU-STD": {"label": "Polynesian Studio", "group": "complement"},
}

API = "https://api.keyholdervacations.com/v2/dvc/availability/calendar/"
RESULTS_URL = ("https://dvcrentalstore.com/guests/availability/results/"
               f"?checkIn={CHECK_IN.isoformat()}&checkOut={CHECK_OUT.isoformat()}")

POLL_MINUTES = 20
JITTER_SECONDS = 30
BACKOFF_MINUTES = 60       # after a 429/5xx, sit out this long
FAIL_ALERT_AFTER = 9       # consecutive all-failed cycles (~3 h) before one error alert

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}

logging.basicConfig(
    filename=LOG_FILE, level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s")


def fmt(night_iso):
    d = date.fromisoformat(night_iso)
    return d.strftime("%b %-d") if sys.platform != "win32" else d.strftime("%b %d").replace(" 0", " ")


def fmt_run(nights):
    """'Jan 26-28' style label for a consecutive run of *nights* (checkout = last night + 1)."""
    last = date.fromisoformat(nights[-1]) + timedelta(days=1)
    return f"{fmt(nights[0])}-{last.strftime('%d').lstrip('0')}"


# --- Acquisition ---------------------------------------------------------

def fetch_room(room_id):
    """Return {night_iso: 'none'|'low'|'high'} for the trip window, or raise."""
    url = (API + urllib.parse.quote(room_id)
           + f"?startDate={CHECK_IN.isoformat()}&endDate={CHECK_OUT.isoformat()}")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.loads(r.read().decode())
    cal = payload.get("data", {}).get("availability")
    if payload.get("statusCode") != 200 or not isinstance(cal, dict):
        raise ValueError(f"unexpected payload for {room_id}: {str(payload)[:200]}")
    return {n: cal.get(n, {}).get("availability", "none") for n in NIGHTS}


def fetch_all():
    """Fetch every watched room. Returns (rooms, errors, backoff_hit)."""
    rooms, errors, backoff_hit = {}, [], False
    for room_id in ROOMS:
        for attempt in (1, 2):
            try:
                rooms[room_id] = fetch_room(room_id)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 or e.code >= 500:
                    backoff_hit = True
                logging.warning("fetch %s HTTP %s (attempt %d)", room_id, e.code, attempt)
                if attempt == 2:
                    errors.append(room_id)
                time.sleep(5)
            except Exception as e:
                logging.warning("fetch %s failed (attempt %d): %s", room_id, attempt, e)
                if attempt == 2:
                    errors.append(room_id)
                time.sleep(5)
        time.sleep(1 + random.random())  # gentle spacing between rooms
    return rooms, errors, backoff_hit


# --- Decision logic ------------------------------------------------------

def is_open(rooms, room_id, night):
    return rooms.get(room_id, {}).get(night, "none") != "none"


def by_group(group):
    return [r for r, m in ROOMS.items() if m["group"] == group]


def full_block(rooms, room_id):
    return all(is_open(rooms, room_id, n) for n in NIGHTS)


def assemble_savanna_split(rooms):
    """Greedy night-by-night assignment across savanna rooms, minimizing switches."""
    plan, current = [], None
    for n in NIGHTS:
        if current and is_open(rooms, current, n):
            plan[-1][1].append(n)
            continue
        for r in by_group("savanna"):
            if is_open(rooms, r, n):
                current = r
                plan.append([r, [n]])
                break
        else:
            return None
    return ", ".join(f"{ROOMS[r]['label']} {fmt_run(ns)}" for r, ns in plan)


def evaluate(rooms):
    """Return (level, description) for the best assembly in current inventory."""
    for r in by_group("savanna"):
        if full_block(rooms, r):
            return 5, f"{ROOMS[r]['label']} — ALL 4 NIGHTS ({fmt_run(NIGHTS)})"
    split = assemble_savanna_split(rooms)
    if split:
        return 4, f"Savanna split covers all 4 nights: {split}"
    for k in (3, 2):
        for r in by_group("savanna"):
            if all(is_open(rooms, r, n) for n in NIGHTS[:k]):
                for c in by_group("complement"):
                    if all(is_open(rooms, c, n) for n in NIGHTS[k:]):
                        return 3, (f"{ROOMS[r]['label']} {fmt_run(NIGHTS[:k])}, "
                                   f"then {ROOMS[c]['label']} {fmt_run(NIGHTS[k:])}")
            if all(is_open(rooms, r, n) for n in NIGHTS[-k:]):
                for c in by_group("complement"):
                    if all(is_open(rooms, c, n) for n in NIGHTS[:-k]):
                        return 3, (f"{ROOMS[c]['label']} {fmt_run(NIGHTS[:-k])}, "
                                   f"then {ROOMS[r]['label']} {fmt_run(NIGHTS[-k:])}")
    for r in by_group("akv_std"):
        if full_block(rooms, r):
            return 2, f"{ROOMS[r]['label']} — all 4 nights ({fmt_run(NIGHTS)})"
    open_sav = [(r, n) for r in by_group("savanna") for n in NIGHTS if is_open(rooms, r, n)]
    if open_sav:
        detail = "; ".join(f"{ROOMS[r]['label']} {fmt(n)}" for r, n in open_sav)
        return 1, f"Savanna nights open (no full assembly): {detail}"
    return 0, "No target availability"


LEVEL_ALERTS = {  # level: (title, pushover priority)
    5: ("AKV SAVANNA AVAILABLE — act now", 1),
    4: ("AKV savanna split — all 4 nights", 1),
    3: ("Savanna split-stay possible", 0),
    2: ("AKV standard studio — 4-night block", 0),
}


def savanna_openings(old_rooms, new_rooms):
    """Savanna nights that flipped closed->open since last run."""
    out = []
    for r in by_group("savanna"):
        for n in NIGHTS:
            was = old_rooms.get(r, {}).get(n, "none") != "none"
            if not was and is_open(new_rooms, r, n):
                out.append((r, n))
    return out


# --- State / notification ------------------------------------------------

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"rooms": {}, "last_level": 0, "best_level": 0,
            "fail_streak": 0, "fail_alerted": False,
            "backoff_until": None, "last_run": None, "last_inventory_log": None}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=1))


def pushover(title, message, url=None, priority=0, dry=False):
    if dry:
        print(f"[DRY] (p{priority}) {title}: {message} {url or ''}")
        return
    creds = json.loads(CREDS_FILE.read_text())
    data = {"token": creds["api_token"], "user": creds["user_key"],
            "title": title, "message": message[:1000], "priority": priority}
    if url:
        data["url"] = url
    req = urllib.request.Request(
        "https://api.pushover.net/1/messages.json",
        data=urllib.parse.urlencode(data).encode(), headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        logging.info("pushover sent (%s, p%d): %s", r.status, priority, title)


def append_inventory_log(state, level, desc):
    today = date.today().isoformat()
    if state.get("last_inventory_log") == today:
        return
    state["last_inventory_log"] = today
    line = f"- {today} dvc_watcher: level {level} — {desc}\n"
    with INVENTORY_LOG.open("a") as f:
        f.write(line)


# --- Cycle ---------------------------------------------------------------

def run_cycle(dry=False):
    state = load_state()
    first_run = not STATE_FILE.exists()

    if state.get("backoff_until"):
        until = datetime.fromisoformat(state["backoff_until"])
        if datetime.now() < until:
            logging.info("in backoff until %s, skipping cycle", until)
            print(f"backing off until {until}")
            return
        state["backoff_until"] = None

    rooms, errors, backoff_hit = fetch_all()

    if backoff_hit:
        state["backoff_until"] = (datetime.now() + timedelta(minutes=BACKOFF_MINUTES)).isoformat()
        logging.warning("server pushback; backing off %d min", BACKOFF_MINUTES)

    if not rooms:  # every room failed
        state["fail_streak"] += 1
        if state["fail_streak"] >= FAIL_ALERT_AFTER and not state["fail_alerted"]:
            pushover("DVC watcher failing",
                     f"All fetches failed {state['fail_streak']} cycles in a row "
                     f"(last errors: {', '.join(errors[:3])}). Check dvc_watcher.log.",
                     dry=dry)
            state["fail_alerted"] = True
        save_state(state)
        print(f"cycle failed ({state['fail_streak']} in a row)")
        return
    if state["fail_streak"]:
        logging.info("recovered after %d failed cycles", state["fail_streak"])
    state["fail_streak"] = 0
    state["fail_alerted"] = False

    old_rooms = state["rooms"]
    # Keep last-known data for rooms whose fetch failed this cycle, so a blip
    # doesn't read as "closed" and re-alert when it comes back.
    merged = dict(old_rooms)
    merged.update(rooms)
    rooms = merged
    level, desc = evaluate(rooms)
    openings = [] if first_run else savanna_openings(old_rooms, rooms)

    alerted = False
    if not first_run and level > state["last_level"] and level in LEVEL_ALERTS:
        title, priority = LEVEL_ALERTS[level]
        note = "" if level >= state["best_level"] else " (seen before; reappeared)"
        pushover(title, desc + note + f"\nBook via DVC Rental Store — window "
                 f"{fmt_run(NIGHTS)}.", RESULTS_URL, priority, dry)
        alerted = True
    elif openings:
        detail = "; ".join(f"{ROOMS[r]['label']} {fmt(n)}" for r, n in openings)
        pushover("Savanna night(s) opened", detail + f"\nCurrent best: {desc}",
                 RESULTS_URL, 0, dry)
        alerted = True

    if level != state["last_level"]:
        logging.info("level %d -> %d: %s", state["last_level"], level, desc)
    state["last_level"] = level
    state["best_level"] = max(state["best_level"], level)
    state["rooms"] = rooms
    state["last_run"] = datetime.now().isoformat(timespec="seconds")
    append_inventory_log(state, level, desc)
    save_state(state)
    logging.info("cycle done: level=%d alerted=%s errors=%s first_run=%s",
                 level, alerted, errors or "none", first_run)
    print(f"cycle done: level {level} — {desc}"
          + (" (seeded baseline)" if first_run else ""))


def show_status():
    if not STATE_FILE.exists():
        print("no state yet — watcher has not run on this machine")
        return
    state = load_state()
    print(f"last run:    {state['last_run']}")
    print(f"level:       {state['last_level']} (best ever: {state['best_level']})")
    print(f"fail streak: {state['fail_streak']}   backoff until: {state['backoff_until']}")
    print(f"nights:      {'  '.join(fmt(n) for n in NIGHTS)}")
    for room_id, cal in state["rooms"].items():
        marks = "  ".join(f"{cal.get(n, '?'):>6}" for n in NIGHTS)
        print(f"{room_id:14} {marks}   {ROOMS.get(room_id, {}).get('label', '')}")


def selftest():
    def rooms_with(spec):
        return {rid: {n: ("low" if n in spec.get(rid, []) else "none")
                      for n in NIGHTS} for rid in ROOMS}
    n1, n2, n3, n4 = NIGHTS
    cases = [
        ("savanna full block", {"AKK-STU-SAV": NIGHTS}, 5),
        ("savanna 2+2 split", {"AKK-STU-SAV": [n1, n2], "AKV-STU-SAV": [n3, n4]}, 4),
        ("savanna 1+3 split", {"AKV-STU-SAV": [n1], "AKK-STU-SAV": [n2, n3, n4]}, 4),
        ("savanna 2 + complement 2", {"AKK-STU-SAV": [n1, n2], "CCV-STU-STD": [n3, n4]}, 3),
        ("complement 2 + savanna 2", {"BLT-STU-STD": [n1, n2], "AKV-STU-SAV": [n3, n4]}, 3),
        ("savanna 1 + complement 3 (below min run)", {"AKK-STU-SAV": [n1], "CCV-STU-STD": [n2, n3, n4]}, 1),
        ("akv standard block", {"AKV-STU-VAL": NIGHTS}, 2),
        ("partial savanna only", {"AKK-STU-SAV": [n2]}, 1),
        ("nothing", {}, 0),
        ("complement-only block (not our room)", {"POL-STU-STD": NIGHTS}, 0),
    ]
    failures = 0
    for name, spec, want in cases:
        got, desc = evaluate(rooms_with(spec))
        ok = "ok " if got == want else "FAIL"
        if got != want:
            failures += 1
        print(f"{ok} {name}: level {got} (want {want}) — {desc}")
    print("openings diff:",
          savanna_openings(rooms_with({}), rooms_with({"AKK-STU-SAV": [n1]})))
    sys.exit(1 if failures else 0)


def main():
    if "--selftest" in sys.argv:
        selftest()
    if "--status" in sys.argv:
        show_status()
        return
    if "--test" in sys.argv:
        pushover("DVC watcher armed",
                 f"Polling {len(ROOMS)} room types for {fmt_run(NIGHTS)} "
                 f"every {POLL_MINUTES} min.")
        print("test notification sent")
        return
    dry = "--dry" in sys.argv
    if "--watch" in sys.argv:
        while True:
            try:
                run_cycle(dry)
            except Exception:
                logging.exception("cycle crashed")
            time.sleep(POLL_MINUTES * 60 + random.uniform(0, JITTER_SECONDS))
    else:
        run_cycle(dry)


if __name__ == "__main__":
    main()
