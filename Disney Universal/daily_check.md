# Daily trip check — instructions for scheduled Claude run

You are running as a scheduled daily job on Tanner's always-on Windows desktop (native CLI, no WSL). Work from the `Trips/Disney Universal` folder. Context: `../CLAUDE.md`, `README.md`, `planning/MASTER-PLAN.md`. Trip: Jan 23–30, 2027 (Universal Jan 23–26 booked at Helios Grand; Disney Jan 26–30 — hunting an AKV Savanna View studio via DVC rental).

**Step 0:** `git pull` in the Trips repo root first — planning updates from the laptop arrive via git.

**Step 0.5 — ONE-TIME: install the DVC watcher schedule** (delete this section once it succeeds). If a Task Scheduler task named `DVC Watcher` does not already exist (`schtasks /query /tn "DVC Watcher"` errors):

1. Run `python dvc_watcher.py` once from this folder (seeds its per-night baseline; first run sends no alerts).
2. Create the task: every **20 minutes**, indefinitely, running `dvc_watcher.py` with this machine's Python — e.g. `schtasks /create /tn "DVC Watcher" /sc minute /mo 20 /tr "<python.exe> \"<full path>\dvc_watcher.py\"" /f` (resolve the real python path with `where python`; working directory doesn't matter, the script uses paths relative to itself).
3. Verify: `schtasks /query /tn "DVC Watcher"` succeeds and `python dvc_watcher.py --status` shows a recent run.
4. Send ONE Pushover alert: `python notify.py "DVC watcher installed" "Desktop now polls DVC availability every 20 min for Jan 26-30."` — this confirms remotely that setup worked.
5. Delete this Step 0.5 section from this file, then `git commit -am "Desktop: DVC watcher installed"` and `git push` so the laptop knows it's done.

If any part fails, alert once with the error and leave this section in place for tomorrow's run. Also: a temporary interim watcher may have been running on the laptop until this installs — duplicate alerts during the overlap are expected and harmless.

Do these four checks, in order. Send Pushover alerts ONLY for findings (rule at bottom) — a quiet day sends nothing.

## 1. Run the deal watcher

```
python deal_watcher.py
```

It handles its own Pushover alerts. If it errors, alert once with the error.

## 2. DVC watcher health check

The DVC inventory hunt is now owned by **`dvc_watcher.py`**, which polls the per-night availability API every 20 minutes via its own Task Scheduler job and sends its own Pushover alerts (savanna block > savanna split > mixed split > standard ladder, edge-triggered — see its docstring). Your job here is only to verify it's alive:

1. Run `python dvc_watcher.py --status`. Healthy = last run within the past hour, fail streak 0.
2. If state is missing, stale (>2 h), or fail streak > 0: run `python dvc_watcher.py` once manually. If that errors too, alert ("DVC watcher down: <one-line reason>") and fall back to the manual check below for today.

**Manual fallback only** (when the watcher is down): open `https://dvcrentalstore.com/guests/availability/results/?checkIn=2027-01-26&checkOut=2027-01-30` with Playwright. Hunting an AKV (Jambo/Kidani) **Deluxe Studio, Savanna View** for Jan 26–30; fallback ladder: savanna 4-night block > Jambo↔Kidani savanna split > savanna ≥2 nights + deluxe studio complement (Copper Creek/Boulder Ridge, Bay Lake Tower, Polynesian) > AKV standard studio block. A mid-stay move with a 6-year-old costs real energy — 2 savanna nights justify it; a lateral move does not. Log findings in `dvc_inventory_log.md`; alert improvements only.

## 3. Helios rate re-shop

Via Playwright, price **Helios Grand Hotel, Jan 23–26, 2027, 2 adults + 1 child** (3 nights) on Universal's booking site (universalorlando.com → hotels, or the Loews booking engine it redirects to). Booked rate: **$471.33/night**. If a standard/refundable rate now shows **below $460/night**, alert with the number ("Helios rebook opportunity: $X/nt vs $471.33 booked"). Log the rate seen in `helios_rate_log.md` (one dated line per run). If the site blocks or errors, log it and stay silent (alert only if it fails 3+ consecutive days).

## 4. DVC email watch (until the AKV room is booked)

If Gmail tools are available in this session, search `from:dvcrentalstore.com newer_than:1d` (also check spam). If a new reply exists, alert with a one-line summary of what it says/asks. If Gmail tools aren't connected on this machine, skip silently.

## Alert rules

- Use `python notify.py "Title" "Message" [url]` for all alerts.
- Findings only — no daily "all quiet" pings, no repeats of yesterday's finding (check the log files first).
- If any step crashes in a way you can't work around, send ONE alert: "Daily check error: <step> — <one-line reason>".
- After the AKV room gets booked (README will say so), steps 2 and 4 are obsolete — if README shows the Disney hotel checked off, skip them and suggest (once) trimming this file.
