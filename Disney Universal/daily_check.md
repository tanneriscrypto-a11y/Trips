# Daily trip check — instructions for scheduled Claude run

You are running as a scheduled daily job on Tanner's always-on Windows desktop (native CLI, no WSL). Work from the `Trips/Disney Universal` folder. Context: `../CLAUDE.md`, `README.md`, `planning/MASTER-PLAN.md`. Trip: Jan 23–30, 2027 (Universal Jan 23–26 booked at Helios Grand; Disney Jan 26–30 — hunting an AKV Savanna View studio via DVC rental).

**Step 0:** `git pull` in the Trips repo root first — planning updates from the laptop arrive via git.

Do these four checks, in order. Send Pushover alerts ONLY for findings (rule at bottom) — a quiet day sends nothing.

## 1. Run the deal watcher

```
python deal_watcher.py
```

It handles its own Pushover alerts. If it errors, alert once with the error.

## 2. DVC inventory check (needs INVENTORY_URL below)

INVENTORY_URL: `https://dvcrentalstore.com/guests/check-dvc-availability/?checkIn=2027-01-26&checkOut=2027-01-30&occupancy=4`

Open it with Playwright browser tools. Rows show per-room status (Available / Partial Availability / No Availability); clicking a row's status pill opens a per-night calendar (green=available, orange=limited, gray=none). Baseline Aug 9, 2026: AKV savanna studio had ONLY Jan 27 (limited) — everything AKV was partial; full-block studios existed only at Saratoga Springs (~$1,122). We are hunting cancellation churn. Check for **Jan 26–30, 2027**:

1. First choice: Animal Kingdom Villas (Jambo or Kidani) **Deluxe Studio, Savanna View**, all 4 nights → if available, ALERT immediately (title "AKV SAVANNA AVAILABLE — act now").
2. If not available as a block, check **resort-hop (split-stay) combinations**, best-first:
   - AKV savanna studio Jambo ↔ Kidani split (any 2+2 or 1+3 covering all 4 nights) — easy hop, same resort grounds
   - AKV savanna for ≥2 nights + another deluxe DVC studio for the rest (check: Wilderness Lodge/Copper Creek, Bay Lake Tower, Polynesian — all better MK access; any is a fine complement)
   - AKV **Standard View** studio, 4 nights (fallback — lodge without the room view)
3. Alert with the best available combination and its nightly breakdown. Track what you saw in `dvc_inventory_log.md` (append one dated line per run: best option seen). Only alert when TODAY'S best option is BETTER than the best previously logged (savanna block > savanna split > mixed split > standard) — improvements only, not repeats.

Resort-hop judgment rule: a split is only worth proposing if it secures savanna-view nights that are otherwise unavailable. A move mid-stay with a 6-year-old costs real energy — 2 savanna nights justify it; a lateral move does not.

## 3. Helios rate re-shop

Via Playwright, price **Helios Grand Hotel, Jan 23–26, 2027, 2 adults + 1 child** (3 nights) on Universal's booking site (universalorlando.com → hotels, or the Loews booking engine it redirects to). Booked rate: **$471.33/night**. If a standard/refundable rate now shows **below $460/night**, alert with the number ("Helios rebook opportunity: $X/nt vs $471.33 booked"). Log the rate seen in `helios_rate_log.md` (one dated line per run). If the site blocks or errors, log it and stay silent (alert only if it fails 3+ consecutive days).

## 4. DVC email watch (until the AKV room is booked)

If Gmail tools are available in this session, search `from:dvcrentalstore.com newer_than:1d` (also check spam). If a new reply exists, alert with a one-line summary of what it says/asks. If Gmail tools aren't connected on this machine, skip silently.

## Alert rules

- Use `python notify.py "Title" "Message" [url]` for all alerts.
- Findings only — no daily "all quiet" pings, no repeats of yesterday's finding (check the log files first).
- If any step crashes in a way you can't work around, send ONE alert: "Daily check error: <step> — <one-line reason>".
- After the AKV room gets booked (README will say so), steps 2 and 4 are obsolete — if README shows the Disney hotel checked off, skip them and suggest (once) trimming this file.
