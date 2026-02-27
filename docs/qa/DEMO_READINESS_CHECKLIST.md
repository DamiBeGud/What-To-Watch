# Demo Readiness Checklist - Task 13

Use this checklist before presenting the Streamlit recommender to non-technical stakeholders.

## Demo setup

- Start app:
  - `docker compose --profile app up -d streamlit_app`
- Confirm service state:
  - `docker compose --profile app ps streamlit_app`
- Open app: `http://localhost:8501`
- Turn on `Show Debug Panel` so timing/fallback data is available if questions come up.

## Prepared demo inputs

Use these concrete examples for consistent live demos:

- Returning user examples:
  - `711`
  - `793`
- Similar-movie source titles:
  - `Toy Story (1995)` (`movieId=1`)
  - `Matrix, The (1999)` (`movieId=2571`)
- New-user liked-title examples:
  - `Toy Story (1995)`
  - `Godfather, The (1972)`
  - optional genre preferences: `Action`, `Drama`

## Demo flow checklist

| ID | Segment | What to do | What to say (talk track) | Pass/Fail | Notes |
| --- | --- | --- | --- | --- | --- |
| D-01 | Intro | Show mode selector and explain three entry modes. | “The app supports returning users, new users, and similar-movie exploration.” | ☐ Pass ☐ Fail | |
| D-02 | Similar-movie quick win | Search/select `Toy Story (1995)`, generate recs. | “This mode is easy to explain: recommendations are similar to the selected title.” | ☐ Pass ☐ Fail | |
| D-03 | New-user guidance | Select 2–3 liked titles + optional genres, generate recs. | “Even without a stored profile, the app can produce a useful shortlist.” | ☐ Pass ☐ Fail | |
| D-04 | Returning-user personalization | Pick user `711`, generate recs. | “Returning-user mode uses stored profile signal when available.” | ☐ Pass ☐ Fail | |
| D-05 | Intentional fallback trigger | New User mode with no likes/genres, generate recs. | “When input is weak, the app is explicit that it used fallback instead of pretending personalization.” | ☐ Pass ☐ Fail | |
| D-06 | Edge-case trust check | Similar Movie mode with no source selected, generate. | “If input is incomplete, the app explains what is missing and still stays stable.” | ☐ Pass ☐ Fail | |
| D-07 | Responsiveness check | Change one filter (genre/year) and rerun. | “The app reloads heavy assets once, then responds quickly to interaction changes.” | ☐ Pass ☐ Fail | |
| D-08 | Observability check | Expand Debug Panel after a request. | “Timing and mode/fallback traces are available for transparency and troubleshooting.” | ☐ Pass ☐ Fail | |

## Fallback explainability check

Confirm at least one fallback run displays all of:

- mode used
- fallback used (true)
- fallback reason or plain-language fallback summary

Result: ☐ Pass ☐ Fail

## Timing/debug readiness check

Confirm debug payload visibility for a live request:

- startup timing block visible
- request timing breakdown visible
- effective performance limits visible (`candidate_pool_*`, `similar_scan_limit`)

Result: ☐ Pass ☐ Fail

## Final go/no-go

- Demo readiness status: ☐ GO ☐ NO-GO
- Blocking issues (if any):
  - 
  - 

