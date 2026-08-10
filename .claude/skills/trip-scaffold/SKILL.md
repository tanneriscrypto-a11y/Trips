---
name: trip-scaffold
description: Create the standard folder structure for a new trip in the Trips workspace. Use when the user starts planning a new vacation, conference, or trip and needs a folder set up.
---

# Trip Scaffold

Create a new trip folder following the house conventions (evolved from the Gen Con trip):

```
Trips/<Trip Name>/
  README.md          # trip summary: dates, travelers, confirmations, links
  planning/          # itineraries, research notes, day plans (markdown)
  data/              # machine state: trackers, logged datasets, *.json state files
  budget.html        # self-contained budget page (copy structure from Gen Con/budget.html)
```

Rules:

- Ask for (or infer from context): trip name, rough dates, travelers, and what needs booking (flights, hotel, tickets, dining).
- Seed `README.md` with a **Booking deadlines** table (item, window opens, booked?) — this is the single most-referenced file during planning.
- For the planning phase itself, hand off to the `travel-agent` plugin's workflow (discovery → options → itinerary → reservations tracker → packing).
- Custom monitors/scripts for the trip live in the trip folder, logs as `<name>.log`, state as `<name>_state.json` (Gen Con pattern).
- Don't commit secrets: credential files (like Gen Con's `*_creds*`) stay out of any future git history.
