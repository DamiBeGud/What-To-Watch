# Manual QA Checklist - Task 13

This checklist is for teammate-run validation of the Streamlit app without reading source code.  
Goal: confirm the app stays clear, stable, and explainable across normal and edge-case flows.

## Preconditions

- Artifacts exist in `artifacts/` (including `user_profiles_train.jsonl`).
- App is running:
  - `docker compose --profile app up -d streamlit_app`
- Open app at `http://localhost:8501`.
- Enable `Show Debug Panel` in the sidebar for checks that mention timing/debug details.

## Checklist

| ID | Scenario | Steps | Expected result | Pass/Fail | Notes |
| --- | --- | --- | --- | --- | --- |
| QA-01 | App startup ready state | Open app and expand `Bootstrap Summary`. | `startup_ready` is true and no setup error banner is shown. | ☐ Pass ☐ Fail | |
| QA-02 | Mode switching | Switch between `Returning User`, `New User / Cold Start`, and `Similar Movie`. | Mode-specific input controls update immediately and retain valid state. | ☐ Pass ☐ Fail | |
| QA-03 | Returning user normal flow | Choose demo user `711`, click `Generate Recommendations`. | Results render with title/year/genres/reason cards; status shows mode used and fallback status. | ☐ Pass ☐ Fail | |
| QA-04 | Returning user fallback flow | In Returning User mode, clear manual user and choose no valid user (or enter unknown ID like `999999`), then generate. | Fallback warning is shown with plain-language explanation and still returns a usable list. | ☐ Pass ☐ Fail | |
| QA-05 | New user strong signal flow | New User mode: search/select `Toy Story (1995)` and `Matrix, The (1999)`, optionally select genres, then generate. | Recommendation list appears with clear reason text; status indicates New User mode. | ☐ Pass ☐ Fail | |
| QA-06 | New user weak-signal fallback | New User mode: leave liked titles and genres empty, then generate. | Clear weak-signal/fallback message appears; recommendations still returned. | ☐ Pass ☐ Fail | |
| QA-07 | Similar movie normal flow | Similar Movie mode: search `Toy Story`, select `Toy Story (1995)`, then generate. | Similar-movie results render; explanation references source-title similarity. | ☐ Pass ☐ Fail | |
| QA-08 | Similar movie no source selected | Similar Movie mode: do not select a source title, generate. | App shows no-source guidance and fallback explanation instead of crashing/blank output. | ☐ Pass ☐ Fail | |
| QA-09 | No title match guidance | New User or Similar Movie mode: search nonsense text like `zzzzzzzz` and generate. | App shows clear no-match guidance with actionable next step. | ☐ Pass ☐ Fail | |
| QA-10 | Strict-filter behavior | Any mode: set narrow filters (example: genre mismatch + single-year range), then generate. | If strict filters remove all items, app explains relaxation/empty behavior and remains usable. | ☐ Pass ☐ Fail | |
| QA-11 | Missing metadata placeholder behavior | Inspect rendered cards for any item with missing year/genres/poster. | App shows placeholders/notes instead of silently dropping results. | ☐ Pass ☐ Fail | |
| QA-12 | Debug timing visibility | With debug panel enabled, run a request in each mode. | Panel shows startup timing, request timing breakdown, and effective performance limits. | ☐ Pass ☐ Fail | |
| QA-13 | Setup failure state (safe simulation) | Create temp copy of artifacts, delete `cf_item_ids.npy`, run validator: `python3 -m src.infrastructure.loaders.startup_validator --artifacts-dir <temp>/artifacts`. | Validation fails with actionable missing-artifact message (file + next-step command). | ☐ Pass ☐ Fail | |

## Plain-language quality check

For at least one fallback run and one edge-case run, confirm the message explains:

- what happened
- why the app changed behavior
- what the user should do next

Result: ☐ Pass ☐ Fail

