# Daily trip check — instructions for scheduled Claude run

You are running as a scheduled daily job on Tanner's always-on Windows desktop (native CLI, no WSL). Work from the `Trips/Disney Universal` folder. Context: `../CLAUDE.md`, `README.md`, `planning/MASTER-PLAN.md`. Trip: Jan 23–30, 2027 (Universal Jan 23–26 booked at Helios Grand; Disney Jan 26–30 — **target split: AKV Savanna View studio Jan 26–28 + Polynesian studio Jan 28–30**. DVC Rental Store request ARF-217165 open ($100 held) for the AKV savanna leg — Kidani was claimed away 8/25 before a member booked it. Poly leg currently closed; the watcher alerts when it opens. Caribbean Beach cash fallback decision Nov 1).

**Step 0:** `git pull` in the Trips repo root first — planning updates from the laptop arrive via git.

**Step 0.5 — ONE-TIME: speed up the DVC watcher schedule** (delete this section once it succeeds). The `DVC Watcher` Task Scheduler job should now run every **5 minutes** (the script itself tiers requests so only race-deciding rooms poll that fast). If the task still shows a 20-minute interval (`schtasks /query /tn "DVC Watcher" /v`):

1. Recreate it: `schtasks /create /tn "DVC Watcher" /sc minute /mo 5 /tr "<same python + script path as before>" /f` (the /f overwrites the existing task; reuse the exact action command from the current task).
2. Verify it fires: wait 5+ minutes, then `python dvc_watcher.py --status` should show a recent last run.
3. Delete this Step 0.5 section, then `git commit -am "Desktop: watcher at 5-min interval"` and `git push`.

If it fails, alert once with the error and leave this section for tomorrow.

Do these four checks, in order. Send Pushover alerts ONLY for findings (rule at bottom) — a quiet day sends nothing.

## 1. Run the deal watcher

```
python deal_watcher.py
```

It handles its own Pushover alerts. If it errors, alert once with the error.

## 2. DVC watcher health check

The DVC hunt is owned by **`dvc_watcher.py`**, which polls the per-night availability API via its own Task Scheduler job (every 5 min for savanna + Poly rooms, ~20 min for the rest) and sends its own Pushover alerts. It hunts the **full window (Jan 26–30)**: savanna 4-night block > Jambo↔Kidani savanna split > savanna ≥2 nights + deluxe complement > any watched deluxe studio 4-night block (edge-triggered — see its docstring). Your job here is only to verify it's alive:

1. Run `python dvc_watcher.py --status`. Healthy = last run within the past hour, fail streak 0.
2. If state is missing, stale (>2 h), or fail streak > 0: run `python dvc_watcher.py` once manually. If that errors too, alert ("DVC watcher down: <one-line reason>") and fall back to the manual check below for today.
3. **Fallback-shrinking check:** the reference rooms (OKW-1BR-STD, RR-1BR-STD, SS-1BR-STD) are the book-anytime full-block fallbacks (all 4 nights open as of 8/26). In the `--status` grid, if any of them no longer covers all 4 nights, alert once ("1BR fallback shrinking: <room> lost <night>") — that's the signal to stop waiting and book. Track in `dvc_inventory_log.md` to avoid repeats.

**Manual fallback only** (when the watcher is down): open `https://dvcrentalstore.com/guests/availability/results/?checkIn=2027-01-26&checkOut=2027-01-30` with Playwright. Hunting an AKV (Jambo/Kidani) **Deluxe Studio, Savanna View** for Jan 26–30; ladder: savanna block > savanna split > savanna ≥2 nights + deluxe complement (Copper Creek/Boulder Ridge, BLT, Poly, Beach Club, BoardWalk, GF, Riviera, AKV standard) > any deluxe 4-night block. A mid-stay move with a 6-year-old costs real energy — 2 savanna nights justify it; a lateral move does not. Log findings in `dvc_inventory_log.md`; alert improvements only.

## 3. Helios rate re-shop

Via Playwright, price **Helios Grand Hotel, Jan 23–26, 2027, 2 adults + 1 child** (3 nights) on Universal's booking site (universalorlando.com → hotels, or the Loews booking engine it redirects to). Booked rate: **$471.33/night**. If a standard/refundable rate now shows **below $460/night**, alert with the number ("Helios rebook opportunity: $X/nt vs $471.33 booked"). Log the rate seen in `helios_rate_log.md` (one dated line per run). If the site blocks or errors, log it and stay silent (alert only if it fails 3+ consecutive days).

## 4. DVC email watch (until the AKV room is booked)

If Gmail tools are available in this session, search `from:dvcrentalstore.com newer_than:1d` (also check spam). If a new reply exists, alert with a one-line summary of what it says/asks. **Critical:** if an email reports the open request (ARF-217165) has been SECURED with a reservation/confirmation number, Tanner must pay the deposit balance and e-sign within **24 hours** or the $100 is forfeit — alert that one at high priority ("DVC RESERVATION SECURED — pay balance within 24h"). If Gmail tools aren't connected on this machine, skip silently.

## Alert rules

- Use `python notify.py "Title" "Message" [url]` for all alerts.
- Findings only — no daily "all quiet" pings, no repeats of yesterday's finding (check the log files first).
- If any step crashes in a way you can't work around, send ONE alert: "Daily check error: <step> — <one-line reason>".
- After the AKV room gets booked (README will say so), steps 2 and 4 are obsolete — if README shows the Disney hotel checked off, skip them and suggest (once) trimming this file.
