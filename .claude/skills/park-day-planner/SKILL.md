---
name: park-day-planner
description: Plan and adjust Disney World / Universal Orlando park days using live wait times, park hours, and historical crowd data. Use when the user asks about wait times, which park to visit on a day, rope-drop or touring plans, park hours, ride closures, or crowd levels.
---

# Park Day Planner

Build touring plans grounded in real data, never guessed wait times.

## Data sources

All `waits.py` commands need no API keys. Park IDs/slugs for every source live at the top of `scripts/waits.py`.

### Historical (for picking parks/days and scheduling headliners)

1. **Thrill Data crowd calendar** — `python3 scripts/waits.py crowdcal <park> [YYYY[-MM]]` — daily average wait per park, **2014 to yesterday**, incl. Epic Universe since its 2025 opening. JSON endpoint: `https://www.thrill-data.com/wa/park-crowdcal/<slug>`. Primary source for "which park on which day" and seasonal comparisons (pull the same month from prior years).
2. **TouringPlans open datasets** — minute-level posted AND actual waits for 14 WDW headliners: `https://cdn.touringplans.com/datasets/<ride>.csv` (e.g. `7_dwarfs_train`, `flight_of_passage`, `slinky_dog`; plus `metadata.csv` with park hours/events per day, and `touringplans_data_dictionary.xlsx`). **Caveat: data spans 2015–2021 only** — great for hour-of-day/day-of-week shape analysis (rope-drop dips, parade dips), but pre-Genie+ era and missing newer rides (TRON, Tiana's, all of Epic Universe). Download to `Disney Universal/data/touringplans/`, analyze with pandas.
3. **Our own log** — `Disney Universal/data/wait_times.csv` (timestamp, park, land, ride, is_open, wait_min), grown via `python3 scripts/waits.py log`. The only per-ride current-era source we fully control; suggest a recurring `/loop` or cron if it looks sparse.
4. **Queue-Times historical charts** — per-ride current-era history, but Cloudflare-protected HTML, NOT reachable via curl. Use Playwright browser tools on `https://queue-times.com/en-US/parks/<id>` ride pages and crowd calendar.
5. **Thrill Data web pages** (via Playwright or curl) — per-ride charts, Lightning Lane availability/pricing history, park hours vs. crowds. Bulk CSV export exists but needs their paid Plus membership — mention it only if deep per-ride current-era data becomes essential.

### Live (for day-of adjustments)

- `python3 scripts/waits.py live <park>` — current waits, sorted longest first (Queue-Times, ~5 min updates)
- `python3 scripts/waits.py hours <park> [YYYY-MM-DD]` — official hours incl. Extra/Early Entry (ThemeParks.wiki)
- **ThemeParks.wiki live entity data** — `https://api.themeparks.wiki/v1/entity/<park-id>/live` includes showtimes, virtual queue state, and (where published) paid Lightning Lane / Express pricing.

## Touring plan rules

- Rope drop beats everything: plan the top-2 headliners in the first hour after open.
- Verify hours with `waits.py hours` for the actual date — never assume 9-9; check for Early Entry (Disney resort guests) and special events (early close for parties).
- Use historical/by-hour data to schedule headliners at their daily wait minimum (usually first hour and last 2 hours).
- Plan around shows/parades from the live entity data — waits dip during parades.
- Always name a backup per time block (weather, breakdowns).
- Output plans as markdown into `Disney Universal/planning/`, one file per park day, with per-block times, walking order by land, and meal stops.

## Attribution

Any user-facing page (HTML planner, artifact) that shows Queue-Times data must display "Powered by Queue-Times.com". Credit Thrill Data and TouringPlans when their data appears in a deliverable.
