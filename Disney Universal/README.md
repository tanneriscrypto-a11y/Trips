# Disney World + Universal Orlando

Status: **research complete, awaiting decisions** (2026-08-09). See `planning/MASTER-PLAN.md` for the full recommendation; detail in `planning/research-*.md` + `planning/crowd-analysis.md`.

## Trip facts

| | |
|---|---|
| Dates | **Jan 23–30, 2027** (marked 23–28, extending into weekend; depart home Sat, return Sat) |
| Travel | **Driving** — Newnan, GA → Orlando, ~7 hrs / ~440 mi via I-75 |
| Travelers | Tanner + MK + River (6); friend Scottie likely (confirm) |
| River's height | **TBD — MEASURE (shoes on)**; 40/42/44/48" thresholds drive everything |
| Budget | Comfort tier, $8–10k (est. ~$8,400) |
| Home base | **Split stay confirmed**, Universal first: Helios Grand or Stella Nova ×3 → Disney moderate ×4 |
| Parks | Epic (Sun) → USF/IOA (Mon) → MK (Tue) → HS (Wed) → AK+EPCOT hopper (Thu) → MK (Fri) |

## Booking deadlines (recompute if dates move from Nov 28 arrival)

| Item | Deadline | Booked? |
|---|---|---|
| Measure River; confirm friends in/out | ASAP | ☐ |
| Universal hotel: **Helios Grand booked** — $471.33/nt × 3 (3 guests). If Scottie confirms: modify reservation to 4 guests (EPA requires registered guests); re-shop if winter promo drops | Done 2026-08-09 | ☑ |
| Disney hotel — **AKV Savanna Studio: NO availability as of 2026-08-09** (only Jan 27 "limited"; all AKV categories partial; DVC Rental Store request declined). **Hunting cancellation churn via daily bot** + their confirmed-listing email alerts. Decision point ~Nov 1: if still nothing, book Caribbean Beach cash fallback (~$1,405 rack, less w/ fall discount) | Bot running; decide Nov 1 | ☐ |
| Universal 3-day park-to-park tickets (reseller; watch 2027 promos) | ~Oct–Nov | ☐ |
| Disney 4-day + Hopper tickets (reseller) | ~Nov | ☐ |
| **Disney ADRs** (Tusker House Thu lunch, Chef Mickey's Fri dinner) | **Nov 27, 2026, 5:45 a.m. ET** | ☐ |
| **Lightning Lane** Multi Pass (MK ×2 + HS) + Rise Single Pass | **Jan 19, 2027, 7 a.m. ET** | ☐ |
| Power-Up Band online; ponchos; winter-evening layers | 2 wks out | ☐ |
| Re-verify Epic EPA/virtual lines + Jan refurb calendar; car service check | 1–2 wks out | ☐ |

## Bots

- `deal_watcher.py` — daily promo/deal watcher → Pushover. Watches: 4 blog RSS feeds for ticket/room promo announcements, 5 deal pages for changes (MouseSavers ×3, Disney special offers, Universal tickets), 3 DVC listing pages for AKV savanna studios. State/log beside it. **Run on the always-on desktop only** (state/logs live beside the script and belong to one machine): Task Scheduler, daily. `--test` sends a pipeline-check push; `--dry` prints instead of pushing.

## Working files

- `planning/` — day plans and research (one markdown file per park day)
- `data/wait_times.csv` — our logged wait-time history (grows via `waits.py log`)
- `budget.html` — TBD, copy structure from `../Gen Con/budget.html`
