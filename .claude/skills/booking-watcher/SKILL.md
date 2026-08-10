---
name: booking-watcher
description: Build a monitor/notifier for a hard-to-get booking — dining reservations, hotel rooms, ticket drops, price drops. Use when the user wants to watch availability or get notified when something opens up.
---

# Booking Watcher

Generalizes the Gen Con housing-sniper pattern into a repeatable recipe.

## Recipe

1. **Find the data source.** Prefer a JSON/API endpoint (watch the network tab via Playwright browser tools while doing a manual search). Fall back to HTML scraping only if no endpoint exists. Disney dining availability, hotel rates, and ticket inventory all have XHR endpoints behind their search UIs.
2. **Write a poller** in the trip folder: `<target>_watcher.py`.
   - State in `<target>_state.json` (last seen availability, last notify time) so restarts don't re-alert.
   - Log to `<target>_watcher.log`.
   - Poll interval: 5–15 min for dining/hotels; respect the site — back off on errors, use realistic headers.
   - Dedupe alerts: notify on *transitions* (unavailable → available), not on every poll.
3. **Notify** the way Gen Con did (`gencon_notifier.py` is the reference implementation) — reuse its channel (email/push) rather than inventing a new one.
4. **Run it** via `nohup` or a scheduled `/loop`, and record the running command in the trip README so it can be found and killed later.

## Cautions

- Watchers *watch and alert*; they must not auto-book anything or bypass CAPTCHAs/anti-bot walls. The human clicks "book". (`open_booking_window.py` in Gen Con is the pattern: alert + open the right page, human completes it.)
- Check login/session expiry: store cookies in the state file, alert loudly when auth dies instead of silently polling logged-out pages.
- Disney-specific: dining opens 60 days before the date (resort guests can book 60 days + length of stay); the best watch window is 05:45–06:15 ET when the day's inventory loads.
