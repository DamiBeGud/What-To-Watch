# Movie Recommendation App (Streamlit + QUAAACK)

## 1. Project Overview (plain language first)
This repository contains a movie recommendation app built for a course/demo setting.  
It helps people quickly find movies they may like, while clearly explaining why each result appears.

For non-technical readers: think of this as a guided movie suggestion tool with three ways to start, plus clear fallback behavior when there is not enough information.

For technical readers: this repo includes QUAAACK phase notebooks, exported serving artifacts, a layered Streamlit app, and tests that cover unit/integration/smoke behavior.

Current implementation status: Tasks 6-13 are implemented in code and docs. Task 14 (packaging/runbook hardening) is the next handover step.

## 2. What This App Does (three recommendation modes + explanations)
The app supports three recommendation modes:

| Mode | Who it is for | What it uses | Typical explanation |
| --- | --- | --- | --- |
| Returning User | People with a known profile/user ID | Stored user profile signals + artifact-backed ranking | "Because this matches your profile preferences..." |
| New User / Cold Start | People without a saved profile | Selected liked titles + optional genres, with fallback if weak | "Using your selected genres/likes..." |
| Similar Movie | People exploring from one title | Source movie metadata similarity | "Similar to _[source title]_ in genre/theme..." |

The app always tries to return a usable list.  
If the signal is weak or missing, it can use **fallback** recommendations (for example, genre-aware or global popularity) and tells the user that it did so.

## 3. Repository Map (clear tree + one-line purpose per major folder/file)
```text
.
|-- streamlit_app.py                  # Streamlit entrypoint (delegates to app.main)
|-- app/                              # UI layer: views, widgets, controllers, presenters, session state
|   |-- main.py                       # Page bootstrap + cached dependency wiring
|   |-- views/home_view.py            # Main page orchestration/render flow
|   |-- controllers/                  # UI request parsing + facade action calls
|   |-- presenters/                   # UI-friendly shaping of response/error payloads
|   |-- components/                   # Reusable UI widgets/cards/status components
|   `-- state/session_state.py        # Streamlit session-state defaults and helpers
|-- src/                              # Backend layers (core/domain/application/infrastructure/serving)
|   |-- core/                         # Config + dependency initialization
|   |-- domain/                       # Request/response DTOs and enums
|   |-- application/services/         # Routing, explanation, filtering, recommendation orchestration
|   |-- infrastructure/               # Artifact loaders, validator, repository implementations
|   `-- serving/api.py                # Stable facade used by UI
|-- artifacts/                        # Offline-generated runtime bundle (validated at startup)
|-- ml-25m/                           # MovieLens source dataset used for offline preparation
|-- tests/                            # Unit, integration, and smoke test suites
|-- docs/qa/                          # Manual QA + demo-readiness checklists
`-- .ai/                              # Project standards: tasks, data contract, architecture, decisions
```

## 4. Architecture Summary (UI -> services -> repositories -> artifacts)
Runtime dependency direction:

`Streamlit UI (app/) -> Serving Facade (src/serving/api.py) -> Application Services -> Repository Ports/Implementations -> Artifacts`

Key points:
- UI remains thin: collects input, triggers controller actions, renders presenter output.
- Business logic stays in `src/application/services/*`.
- File/artifact access stays in `src/infrastructure/*`.
- `src/serving/api.py` is the stable UI contract.

Public facade methods (stable contract):
- `get_app_status()`
- `get_ui_options()`
- `search_titles(query, limit)`
- `recommend(request_dict)`

`recommend(request_dict)` response shape (stable keys):
- `ok`
- `mode_used`
- `fallback_used`
- `status_message`
- `warnings`
- `items`
- `debug`

Common additional keys include `mode_requested` and `fallback_reason`.

## 5. Data and Artifacts (what comes from `ml-25m`, what is generated in `artifacts/`)
### Source data (`ml-25m/`)
| File | Used for |
| --- | --- |
| `ratings.csv` | User-item interaction signal |
| `movies.csv` | Movie title/genre metadata |
| `tags.csv` | Optional enrichment for future iterations |
| `links.csv` | External IDs for potential metadata/poster extension |
| `genome-tags.csv` + `genome-scores.csv` | Advanced content signals (optional/heavier path) |
| `README.txt` | Dataset limits and provenance |

### Generated serving artifacts (`artifacts/`)
| File | Purpose at runtime |
| --- | --- |
| `movie_metadata.csv` | Display metadata for cards and filters |
| `global_popularity_train.csv` | Global fallback ranking source |
| `genre_popularity_train.csv` | Genre-aware fallback and cold-start behavior |
| `genre_features.npz` + `genre_feature_columns.json` | Content/similarity features |
| `cf_item_similarity.npz` + `cf_item_ids.npy` | Collaborative similarity lookup |
| `user_profiles_train.jsonl` | Returning-user profile signals |
| `aaa_selected_params.json` | Selected serving parameters |
| `aaa_artifact_manifest.json` | Artifact contract manifest |
| `aaa_export_provenance.json` | Export provenance metadata |

Important runtime rule: the Streamlit app serves from `artifacts/`; it does not parse raw `ml-25m` files on each user interaction.

## 6. Quick Start
### Docker path (recommended)
```bash
cd /Users/damibegud/uni/python
docker compose --profile app up -d streamlit_app
docker compose --profile app ps streamlit_app
```

Open: `http://localhost:8501`

### Local path
```bash
cd /Users/damibegud/uni/python
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r .docker/requirements-streamlit.txt
python3 -m src.infrastructure.loaders.startup_validator --artifacts-dir artifacts
```

## 7. Running the App (exact commands)
### Docker
```bash
cd /Users/damibegud/uni/python
docker compose --profile app up -d streamlit_app
docker compose --profile app logs --tail=200 streamlit_app
```

### Local Streamlit run
```bash
cd /Users/damibegud/uni/python
source .venv/bin/activate
PYTHONPATH=. ARTIFACTS_DIR=artifacts streamlit run streamlit_app.py --server.port 8501
```

## 8. Running Tests (unit/integration/smoke commands)
Run all tests:
```bash
cd /Users/damibegud/uni/python
python3 -m unittest discover -s tests -v
```

Run by scope:
```bash
python3 -m unittest discover -s tests/unit -v
python3 -m unittest discover -s tests/integration -v
python3 -m unittest discover -s tests/smoke -v
```

Optional compile sanity:
```bash
PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m py_compile $(rg --files src app tests | tr '\n' ' ')
```

Docker test run:
```bash
docker compose --profile app exec -T streamlit_app python -m unittest discover -s tests -v
```

## 9. Demo Guide (short script for non-technical walkthrough)
Use this 5-7 minute flow:

1. Open the app and show the three modes.
2. Run **Similar Movie** with `Toy Story (1995)` for a quick, easy-to-understand result.
3. Run **New User / Cold Start** with 2-3 liked titles and optional genres.
4. Run **Returning User** with demo user `711`.
5. Trigger fallback intentionally: New User mode with no likes/genres, then explain that fallback keeps results usable.
6. Trigger one edge case: Similar Movie mode with no source selected.
7. Expand the Debug Panel to show timing and mode/fallback trace.

Prepared examples and talk track checkboxes:
- [docs/qa/DEMO_READINESS_CHECKLIST.md](/Users/damibegud/uni/python/docs/qa/DEMO_READINESS_CHECKLIST.md)

## 10. Troubleshooting (common setup and artifact errors with fixes)
| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Setup error banner at startup | Missing/invalid artifact file or schema | Run `python3 -m src.infrastructure.loaders.startup_validator --artifacts-dir artifacts`, then regenerate artifacts if needed: `python3 -m src.infrastructure.loaders.artifact_exporter --artifacts-dir artifacts` |
| `ModuleNotFoundError: No module named 'app.controllers.ui_actions'` | Outdated container/image or stale checkout | Ensure `app/controllers/ui_actions.py` exists, then rebuild/restart app container: `docker compose --profile app up -d --build streamlit_app` |
| Integration/smoke tests skipped on host | Missing local runtime deps (`numpy`, `pandas`) | Install local deps: `pip install -r .docker/requirements-streamlit.txt` |
| No title match found | Search query is too narrow or misspelled | Try shorter text or alternative spelling |
| No similar-movie results after submit | Source movie not selected | Select a source title first in Similar Movie mode |
| Empty list after filters | Filters are too strict | Widen year range and/or reduce genre restrictions |

Manual QA execution checklist:
- [docs/qa/MANUAL_QA_CHECKLIST.md](/Users/damibegud/uni/python/docs/qa/MANUAL_QA_CHECKLIST.md)

## 11. Limitations and Next Steps (v1 constraints + future tasks)
Known v1 limitations:
- Data is historical (`ml-25m` ends in 2019), so recommendations are not real-time.
- Poster URLs are optional; placeholders are shown when unavailable.
- Fallback can rely on popularity-style signals, which may reduce personalization quality.
- This is a Streamlit demo architecture, not a production-scaled API service.
- No dedicated packaged dependency manifest at repo root yet (`requirements.txt`/`pyproject.toml`), which is part of Task 14 scope.

Next steps:
1. Complete Task 14 packaging/runbook handover.
2. Add broader CI automation and richer regression coverage.
3. Consider stronger content features and deeper explainability once runtime bounds are preserved.

## 12. Glossary (short plain-language definitions)
| Term | Plain-language meaning |
| --- | --- |
| Recommendation mode | The path the app uses to generate suggestions (returning user, new user, similar movie). |
| Fallback | A safe backup recommendation path used when the preferred path lacks enough signal. |
| Cold-start | Situation where the system has little or no user history. |
| Recommendation reason | Human-readable text explaining why an item appears. |
| Artifact | A precomputed file exported offline and loaded at app runtime. |
| Startup validation | Pre-run checks that required artifacts exist and have expected structure. |
| Facade (`src/serving/api.py`) | The stable backend interface the UI calls. |
| Debug panel | Optional UI section that shows request trace, timings, and limits for troubleshooting. |
