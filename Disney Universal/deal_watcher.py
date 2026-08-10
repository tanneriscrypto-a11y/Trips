#!/usr/bin/env python3
"""Daily deal/promo watcher for the Jan 2027 Disney+Universal trip.

Checks (each fails gracefully and logs):
  1. Theme-park blog RSS feeds for ticket/room promo announcements (keyword match)
  2. Deal pages for content changes (MouseSavers, Universal & Disney special offers)
  3. DVC Shop confirmed-reservation listings for AKV savanna studios

Alerts via Pushover (creds in pushover_creds.json beside this script).
State in deal_watcher_state.json; log in deal_watcher.log.

Usage:
  deal_watcher.py            normal run (first run seeds state, no alerts)
  deal_watcher.py --dry      print would-be alerts, send nothing
  deal_watcher.py --test     send a test Pushover notification and exit

Schedule daily, ~8am ET (promos usually announced mornings):
  WSL/Linux cron:  0 8 * * * python3 "/path/to/Disney Universal/deal_watcher.py"
  Windows Task Scheduler: py.exe "C:\\...\\Disney Universal\\deal_watcher.py"
Run it on ONE machine only; state/log files belong to that machine (don't sync them).
"""
import hashlib
import json
import logging
import pathlib
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
STATE_FILE = HERE / "deal_watcher_state.json"
LOG_FILE = HERE / "deal_watcher.log"
CREDS_FILE = HERE / "pushover_creds.json"

# --- What we're shopping for (tune keywords as decisions change) ---
KEYWORDS = re.compile(
    r"(ticket (offer|deal|discount|promo)|special offer|room (offer|discount)|"
    r"4-park magic|buy \d+ (days? )?get \d+|days? free|percent off|% off|"
    r"vacation package.{0,40}(save|off)|annual pass sale)",
    re.I,
)
BRANDS = re.compile(r"universal|disney|epic universe|walt disney world|wdw", re.I)

FEEDS = [
    "https://www.disneytouristblog.com/feed/",
    "https://allears.net/feed/",
    "https://wdwnt.com/feed/",
    "https://blogmickey.com/feed/",
]

DIFF_PAGES = {
    "MouseSavers WDW ticket discounts":
        "https://www.mousesavers.com/walt-disney-world-vacation-discounts-and-deals/walt-disney-world-ticket-discounts/",
    "MouseSavers WDW hotel discounts":
        "https://www.mousesavers.com/walt-disney-world-vacation-discounts-and-deals/disney-world-resort-hotel-discounts-codes/",
    "MouseSavers Universal discounts":
        "https://www.mousesavers.com/universal-orlando-discounts-and-deals/",
    "Disney special offers":
        "https://disneyworld.disney.go.com/special-offers/",
    "Universal Orlando ticket deals":
        "https://www.universalorlando.com/web/en/us/tickets-packages",
}

DVC_LISTING_PAGES = {
    "DVC Shop AKV listings": "https://rentals.dvcshop.com/resorts/animal-kingdom-villas/",
    "DVC Shop AKV Kidani listings": "https://rentals.dvcshop.com/resorts/animal-kingdom-villas-kidani-village/",
    "DVC Rental Store confirmed reservations (our window)":
        "https://dvcrentalstore.com/guests/reservations/?checkIn=2027-01-20&checkOut=2027-02-02&occupancy=4&minNights=2&maxNights=8",
}
DVC_MATCH = re.compile(r"(savanna).{0,400}?(studio)|(studio).{0,400}?(savanna)", re.I | re.S)

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}

logging.basicConfig(
    filename=LOG_FILE, level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s")


def get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"seen_rss": [], "page_hashes": {}, "dvc_seen": []}


def save_state(state):
    state["seen_rss"] = state["seen_rss"][-2000:]
    STATE_FILE.write_text(json.dumps(state, indent=1))


def pushover(title, message, url=None, dry=False):
    if dry:
        print(f"[DRY] {title}: {message} {url or ''}")
        return
    import urllib.parse
    creds = json.loads(CREDS_FILE.read_text())
    data = {"token": creds["api_token"], "user": creds["user_key"],
            "title": title, "message": message[:1000]}
    if url:
        data["url"] = url
    req = urllib.request.Request(
        "https://api.pushover.net/1/messages.json",
        data=urllib.parse.urlencode(data).encode(), headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        logging.info("pushover sent (%s): %s", r.status, title)


def check_feeds(state, first_run, dry):
    for feed_url in FEEDS:
        try:
            root = ET.fromstring(get(feed_url))
            for item in root.iter("item"):
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                guid = (item.findtext("guid") or link or title).strip()
                if guid in state["seen_rss"]:
                    continue
                state["seen_rss"].append(guid)
                if first_run:
                    continue
                if KEYWORDS.search(title) and BRANDS.search(title):
                    pushover("Trip deal news", title, link, dry)
                    logging.info("RSS hit: %s (%s)", title, link)
        except Exception as e:
            logging.warning("feed failed %s: %s", feed_url, e)


def page_fingerprint(html):
    # Strip tags/whitespace/digits-heavy noise so trivial rerenders don't ping
    text = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return hashlib.sha256(text.encode()).hexdigest()


def check_diff_pages(state, first_run, dry):
    for name, url in DIFF_PAGES.items():
        try:
            fp = page_fingerprint(get(url))
            old = state["page_hashes"].get(name)
            state["page_hashes"][name] = fp
            if old and old != fp and not first_run:
                pushover(f"Deal page changed: {name}",
                         "Content changed — check for new offers.", url, dry)
                logging.info("page change: %s", name)
            elif not old:
                logging.info("seeded page: %s", name)
        except Exception as e:
            logging.warning("page failed %s: %s", name, e)


def check_dvc_listings(state, first_run, dry):
    for name, url in DVC_LISTING_PAGES.items():
        try:
            html = get(url)
            hits = DVC_MATCH.findall(html)
            key = f"{name}:{len(hits)}"
            if hits and key not in state["dvc_seen"]:
                state["dvc_seen"].append(key)
                if not first_run:
                    pushover("AKV savanna studio listing?",
                             f"{name} mentions savanna studio ({len(hits)} match(es)) — "
                             "check dates (want Jan 26-30).", url, dry)
            logging.info("dvc %s: %d matches", name, len(hits))
        except Exception as e:
            logging.warning("dvc page failed %s: %s", name, e)


def main():
    dry = "--dry" in sys.argv
    if "--test" in sys.argv:
        pushover("Deal watcher armed",
                 "Daily watcher for Jan 2027 trip is running. "
                 "Watching: promo feeds, deal pages, AKV listings.")
        print("test notification sent")
        return
    state = load_state()
    first_run = not STATE_FILE.exists()
    check_feeds(state, first_run, dry)
    check_diff_pages(state, first_run, dry)
    check_dvc_listings(state, first_run, dry)
    save_state(state)
    logging.info("run complete (first_run=%s dry=%s)", first_run, dry)
    print("run complete", "(seeded baseline)" if first_run else "")


if __name__ == "__main__":
    main()
