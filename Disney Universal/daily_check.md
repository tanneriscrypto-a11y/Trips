# Daily trip check — instructions for scheduled Claude run

You are running as a scheduled daily job on Tanner's always-on Windows desktop (native CLI, no WSL). Work from the `Trips/Disney Universal` folder. Context: `../CLAUDE.md`, `README.md`, `planning/MASTER-PLAN.md`. Trip: Jan 23–30, 2027 (Universal Jan 23–26 booked at Helios Grand; Disney front half **Kidani savanna studio Jan 26–28 requested via DVC Rental Store** — ARF-217165, $100 deposit paid 8/24, awaiting member match/reservation number; back half Jan 28–30 still hunting, Caribbean Beach cash fallback decision Nov 1).

**Step 0:** `git pull` in the Trips repo root first — planning updates from the laptop arrive via git.

Do these four checks, in order. Send Pushover alerts ONLY for findings (rule at bottom) — a quiet day sends nothing.

## 1. Run the deal watcher

```
python deal_watcher.py
```

It handles its own Pushover alerts. If it errors, alert once with the error.

## 2. DVC watcher health check

The DVC hunt is owned by **`dvc_watcher.py`**, which polls the per-night availability API every 20 minutes via its own Task Scheduler job and sends its own Pushover alerts. It now hunts the **back half only (nights Jan 28 + 29)**: Kidani savanna extension (no move) > any savanna > other deluxe studio block > Kidani 1-night extension (edge-triggered — see its docstring). Your job here is only to verify it's alive:

1. Run `python dvc_watcher.py --status`. Healthy = last run within the past hour, fail streak 0.
2. If state is missing, stale (>2 h), or fail streak > 0: run `python dvc_watcher.py` once manually. If that errors too, alert ("DVC watcher down: <one-line reason>") and fall back to the manual check below for today.

**Manual fallback only** (when the watcher is down): open `https://dvcrentalstore.com/guests/availability/results/?checkIn=2027-01-28&checkOut=2027-01-30` with Playwright. Hunting nights Jan 28–30: best is **Kidani Savanna Studio** (extends the existing front-half reservation — zero moves), then Jambo savanna, then any deluxe studio (Copper Creek/Boulder Ridge, Bay Lake Tower, Polynesian, AKV standard, Saratoga, Riviera). Log findings in `dvc_inventory_log.md`; alert improvements only.

## 3. Helios rate re-shop

Via Playwright, price **Helios Grand Hotel, Jan 23–26, 2027, 2 adults + 1 child** (3 nights) on Universal's booking site (universalorlando.com → hotels, or the Loews booking engine it redirects to). Booked rate: **$471.33/night**. If a standard/refundable rate now shows **below $460/night**, alert with the number ("Helios rebook opportunity: $X/nt vs $471.33 booked"). Log the rate seen in `helios_rate_log.md` (one dated line per run). If the site blocks or errors, log it and stay silent (alert only if it fails 3+ consecutive days).

## 4. DVC email watch (until the AKV room is booked)

If Gmail tools are available in this session, search `from:dvcrentalstore.com newer_than:1d` (also check spam). If a new reply exists, alert with a one-line summary of what it says/asks. **Critical right now:** when the email contains a reservation/confirmation number for ARF-217165, Tanner must pay the remaining $131 deposit and e-sign within **24 hours** or the $100 is forfeit — alert that one at high priority ("DVC RESERVATION SECURED — pay balance within 24h"). If Gmail tools aren't connected on this machine, skip silently.

## Alert rules

- Use `python notify.py "Title" "Message" [url]` for all alerts.
- Findings only — no daily "all quiet" pings, no repeats of yesterday's finding (check the log files first).
- If any step crashes in a way you can't work around, send ONE alert: "Daily check error: <step> — <one-line reason>".
- After the AKV room gets booked (README will say so), steps 2 and 4 are obsolete — if README shows the Disney hotel checked off, skip them and suggest (once) trimming this file.
