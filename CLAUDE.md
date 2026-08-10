# Trips

Family vacation-planning workspace. One folder per trip; this is not a software project — deliverables are plans, trackers, and small purpose-built tools.

## Layout

- `Gen Con/` — completed 2026 trip. Reference implementation for the house patterns: monitors/snipers (`housing_sniper.py`), notifier (`gencon_notifier.py`), flight tracker, local itinerary server (`itinerary_server.py` + `planner.html` via cloudflared), `budget.html`.
- `Disney Universal/` — current trip being planned (Walt Disney World + Universal Orlando).
- New trips: use the `trip-scaffold` skill (README with booking-deadlines table, `planning/`, `data/`, `budget.html`).

## Conventions

- Trip scripts live in the trip folder: `<name>.py` with `<name>_state.json` + `<name>.log` beside it.
- Plans and research are markdown in `<trip>/planning/`; machine data (logged datasets, tracker state) in `<trip>/data/`.
- Credential files (`*creds*`, `*key*.txt`) exist in trip folders — never publish, commit, or copy them elsewhere.
- Budget pages are self-contained HTML (`budget.html`), phone-friendly.

## Cross-machine continuity

This folder lives on Tanner's WSL laptop and is NOT currently synced anywhere (the "conflicted copy" files in Gen Con are Dropbox fossils from an earlier location). Cross-machine transfer to the always-on Windows desktop (native CLI): mechanism TBD — git (recommended) or Dropbox. Everything needed to resume work lives IN this folder — trip READMEs, `planning/` docs, bot scripts. Claude memory does NOT transfer between machines; if you lack context, read `Disney Universal/README.md` → `planning/MASTER-PLAN.md` first. Bots and their state/log files run on ONE machine only (the desktop) and their state/logs stay local to it.

**Desktop daily job** (Windows Task Scheduler, ~8:00 AM daily, from the Trips folder):
```
claude -p "Follow the instructions in 'Disney Universal/daily_check.md'"
```
Requires on the desktop: Claude Code CLI with the Playwright plugin, Python 3 on PATH. The job runs `deal_watcher.py`, checks DVC inventory for the AKV savanna studio (Jan 26-30, 2027), re-shops the Helios rate, and Pushover-alerts findings only.

## Tooling

- **travel-agent plugin** (installed, user scope): 7-phase planning workflow — discovery → destination options → logistics → day-by-day itinerary → reservations tracker → packing → PDF. Use it for the planning phase of any trip.
- **Project skills** (`.claude/skills/`):
  - `park-day-planner` — WDW/Universal touring plans from live + historical wait-time data (`scripts/waits.py`; Queue-Times + ThemeParks.wiki live, Thrill Data crowd calendar 2014–present, TouringPlans per-ride CSVs 2015–2021; no API keys).
  - `trip-scaffold` — new-trip folder setup.
  - `booking-watcher` — recipe for availability monitors/notifiers (Gen Con sniper pattern).
- Wait-time history accumulates in `Disney Universal/data/wait_times.csv` — run `python3 .claude/skills/park-day-planner/scripts/waits.py log` snapshots regularly (a recurring /loop or cron helps).
- Queue-Times data shown to users requires a "Powered by Queue-Times.com" credit.
