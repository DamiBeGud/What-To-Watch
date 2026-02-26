# ARCHITECTURE.md - Streamlit App Architecture for the Movie Recommendation App

## Purpose
This document defines the implementation architecture for the Streamlit app that serves the recommender selected in `C-Phase.ipynb` and handed off in `K-Phase.ipynb`.

The goal is to keep the app professional, maintainable, and testable by separating:
- UI/view code (Streamlit widgets and rendering)
- application services (routing, orchestration, explanations)
- repositories/infrastructure (artifact loading and file access)
- domain models/contracts (request and response types)
- offline artifacts (precomputed files created outside the app runtime)

This architecture is intentionally pragmatic. It is designed for a Streamlit demo application, not a large microservice platform, but it still enforces clear boundaries so the recommender logic does not become tangled with UI code.

## Design Principles (Plain Language)
The app should behave like a thin interactive shell around precomputed recommendation assets. Streamlit handles user input and rendering, while backend services decide which recommendation mode to run and how to explain the results. File parsing and artifact validation happen in one place so errors are easier to diagnose.

In practice, this means the app should not retrain models or rebuild large matrices when a user clicks a button. The heavy work is done offline, and the app loads prepared artifacts and uses them to rank and explain recommendations quickly.

## Layered Architecture (Required Direction)

**Dependency direction:** `UI/View -> Application Services -> Repositories/Infrastructure -> Artifacts`

### Why this direction matters
This direction keeps UI code simple and prevents direct file I/O, matrix logic, or recommendation heuristics from spreading into Streamlit views. It also makes the recommendation logic testable without running Streamlit.

## Proposed Project Structure
The exact filenames may evolve, but the separation below should remain stable.

```text
/Users/damibegud/uni/python
|-- streamlit_app.py                 # Optional root entrypoint (delegates to app/main.py)
|-- app/
|   |-- main.py                      # Streamlit bootstrap + page routing
|   |-- views/
|   |   |-- home_view.py
|   |   |-- personalized_view.py
|   |   |-- cold_start_view.py
|   |   |-- similar_movie_view.py
|   |   `-- debug_view.py            # Optional
|   |-- components/
|   |   |-- filters.py
|   |   |-- search_box.py
|   |   |-- recommendation_cards.py
|   |   |-- explanation_panel.py
|   |   `-- status_messages.py
|   |-- controllers/
|   |   |-- request_parser.py
|   |   `-- ui_actions.py
|   |-- presenters/
|   |   |-- recommendation_presenter.py
|   |   `-- error_presenter.py
|   `-- state/
|       `-- session_state.py
|-- src/
|   |-- core/
|   |   |-- config.py
|   |   |-- logging.py
|   |   `-- dependencies.py
|   |-- domain/
|   |   |-- models.py
|   |   |-- requests.py
|   |   |-- responses.py
|   |   `-- enums.py
|   |-- application/
|   |   |-- services/
|   |   |   |-- recommendation_service.py
|   |   |   |-- routing_service.py
|   |   |   |-- explanation_service.py
|   |   |   |-- search_service.py
|   |   |   `-- filter_service.py
|   |   `-- ports/
|   |       |-- repositories.py
|   |       `-- rankers.py
|   |-- infrastructure/
|   |   |-- repositories/
|   |   |   |-- movie_metadata_repository.py
|   |   |   |-- popularity_repository.py
|   |   |   |-- genre_popularity_repository.py
|   |   |   |-- similarity_repository.py
|   |   |   |-- user_profile_repository.py
|   |   |   `-- artifact_manifest_repository.py
|   |   |-- loaders/
|   |   |   |-- artifact_loader.py
|   |   |   `-- startup_validator.py
|   |   |-- rankers/
|   |   |   |-- hybrid_ranker.py
|   |   |   |-- collaborative_ranker.py
|   |   |   |-- content_ranker.py
|   |   |   `-- fallback_ranker.py
|   |   `-- cache/
|   |       `-- streamlit_cache_wrappers.py
|   `-- serving/
|       `-- api.py                   # Thin facade used by Streamlit UI
|-- artifacts/                       # Offline-exported artifacts (app runtime inputs)
|-- tests/
|   |-- unit/
|   |-- integration/
|   `-- smoke/
`-- ml-25m/                          # Raw dataset (avoid direct app runtime dependency if possible)
```

This structure shows where UI code ends and backend logic begins. The app reads from `artifacts/` through repositories, not directly from `ml-25m/` in normal runtime operation.

## Layer Responsibilities

### `app/` (UI/View Layer)
This layer owns Streamlit widgets, layout, session state interactions, and rendering. It should collect user input, display outputs, and present messages, but it should not implement ranking logic or parse artifact files.

Use this layer for:
- mode selection UI (returning user, new user, similar movie)
- filters and search widgets
- result cards and explanation panels
- user-facing error messages and status banners
- `st.session_state` helpers

Avoid in this layer:
- loading CSV/NPZ/JSON artifacts directly
- recommendation scoring logic
- fallback decision rules
- complex data transformations that should be reusable in tests

### `src/domain/` (Domain Models and Contracts)
This layer defines the request and response types used between UI and services, plus enums for modes and fallback reasons. It should be framework-light so it can be reused in tests and service code without importing Streamlit.

Examples:
- `RecommendationMode`
- `FallbackReason`
- `RecommendationRequest`
- `RecommendationResponse`
- `RecommendationItem`

### `src/application/services/` (Application Service Layer)
This layer orchestrates recommendation behavior. It decides how requests move through validation, routing, candidate generation, ranking, explanation formatting, filtering, and result assembly.

Use this layer for:
- routing to personalized / cold-start / similar-movie mode
- fallback escalation when signals are weak
- explanation generation and formatting policy
- filter application and controlled relaxation
- producing a response DTO for the UI

This layer should depend on ports (interfaces), not concrete file loaders.

### `src/application/ports/` (Abstractions)
This layer defines the interfaces used by application services so services can remain independent of file formats and storage details.

Typical port categories:
- repository ports (metadata, popularity, user profiles, manifest)
- ranker ports (hybrid, content, collaborative, fallback)

### `src/infrastructure/` (Repositories, Loaders, Rankers)
This layer implements the concrete file access and ranking primitives. It reads `artifacts/`, validates schemas, builds lookups, and exposes repository/ranker implementations that satisfy application ports.

Sub-areas:
- `loaders/`: artifact loading and startup validation
- `repositories/`: file-backed repositories for metadata, popularity tables, and user profiles
- `rankers/`: hybrid/content/collaborative/fallback ranker implementations
- `cache/`: optional wrappers that isolate Streamlit-specific caching boundaries

### `src/serving/api.py` (Service Facade)
This is the narrow integration surface between Streamlit and the backend. The UI should call a small number of facade functions (for example `recommend(...)`, `search_titles(...)`, `get_app_status(...)`) instead of reaching into many service classes directly.

### `src/core/` (Shared Runtime Wiring)
This layer holds config, logging, and dependency wiring. It is the right place for artifact path configuration, environment toggles, and dependency assembly used by `app/main.py` and `src/serving/api.py`.

## Dependency Direction Rules (Required)

### Allowed dependencies
- `app/*` -> `src/serving/api.py` (or explicit controller/presenter helpers) -> `src/application/*`
- `src/application/*` -> `src/domain/*`, `src/application/ports/*`
- `src/infrastructure/*` -> `src/application/ports/*`, `src/domain/*`, `src/core/*`
- `src/serving/api.py` -> `src/application/*`, `src/infrastructure/*`, `src/core/*`

### Disallowed dependencies (important)
- `app/views/*` importing artifact loaders or reading files from `artifacts/`
- `src/application/services/*` importing Streamlit (`streamlit as st`)
- `src/domain/*` importing Streamlit or pandas-heavy I/O code
- `src/infrastructure/*` importing `app/views/*`

These rules prevent circular dependencies and keep the UI replaceable. They also make the recommender behavior easier to test in isolation.

## Request Flow (Runtime Behavior)

Use this request flow as the default design contract:

```text
View -> Controller -> RecommendationService -> RoutingService
     -> Ranker(s) + Repositories -> Response DTO -> Presenter -> View
```

### Flow meaning in plain language
The UI view collects the user's choices. The controller converts them into a clean request. The recommendation service orchestrates the backend work and asks the routing service which mode to use. The service then uses repositories and rankers to build recommendations, packages the result into a response object, and sends it back to a presenter that formats it for display.

This flow matters because it separates user interaction, recommendation logic, and rendering. If a bug appears in explanations or fallback behavior, you can fix it in services or presenters without rewriting the UI layout.

## Mode Routing and Fallback Design (v1)
This architecture supports the v1 system chosen in `C-Phase.ipynb` and described in `K-Phase.ipynb`.

### Personalized mode (default when usable history exists)
- Primary engine: hybrid recommender (`hybrid_v1_candidate` behavior implemented as a service + rankers)
- Inputs: user profile/history or sufficient liked-movie seed set
- Output: ranked Top-N list with explanations such as "Because you liked X"

### Cold-start mode (new user or weak signal)
- First fallback: genre-aware popularity
- Second fallback: global popularity
- Trigger conditions: missing user history, too few seeds, or no stable personalized candidates
- Output: usable Top-N list plus clear status message indicating fallback usage

### Similar-movie mode (title-to-title exploration)
- Primary engine: content-based title similarity (genre-driven for v1)
- Inputs: selected source movie
- Output: "Similar to Z" recommendations with plain-language reasons

### Fallback behavior (required reliability feature)
Fallback is a first-class feature, not an error case. The response DTO should include:
- mode used
- fallback used (yes/no)
- fallback reason (enum/string)
- warnings or notes shown in the UI

This makes the app more trustworthy because the UI can explain when it used a simpler path instead of silently changing behavior.

## Artifact / Runtime Separation (Non-Negotiable)
This project follows the rule that heavy training and preprocessing are offline responsibilities. The Streamlit app is a serving layer.

### Offline side (not in request path)
- train/evaluate models in notebooks or scripts
- export artifacts to `artifacts/`
- generate metadata, popularity, similarity, and config files
- generate compact user-profile artifact for returning-user mode

### Runtime side (Streamlit app)
- validate required artifacts at startup
- load cached artifacts/resources
- parse UI requests
- route, rank, explain, filter, and render

### Recommended additional artifact for returning-user mode
To support a true returning-user experience without loading full `ml-25m/ratings.csv` at runtime, add a compact artifact such as:
- `artifacts/user_profiles_train.parquet`

Suggested contents:
- `userId`
- seen movie IDs (compact serialized form or normalized table)
- positive seed movie IDs
- preferred genres (optional precomputed)
- interaction counts / simple profile stats

## Artifact Contract and Startup Validation
Startup validation should fail fast with clear messages if required artifacts are missing or incompatible.

### Minimum startup checks
- required files exist in `artifacts/`
- metadata columns required by UI exist (`movieId`, `title`, `genres`, optional `year`)
- similarity matrices and ID arrays are shape-compatible
- `aaa_selected_params.json` contains expected keys
- `aaa_artifact_manifest.json` is readable and consistent with available files

### Failure behavior
- Developer-facing: precise error message naming the missing/invalid file and expected path
- User-facing (if app UI already loads): short setup error panel instead of stack trace dump

This protects demo reliability and reduces debugging time when artifacts are regenerated.

## Caching Boundaries (Streamlit)
Caching is required for responsiveness, but caching must be applied at the right layer boundaries.

### `st.cache_resource` (heavy immutable resources)
Use for:
- loaded metadata table and lookup maps (if large)
- CF similarity matrix and associated ID arrays
- genre feature matrix and associated lookup maps
- repository/service objects assembled at startup

### `st.cache_data` (deterministic derived data)
Use for:
- title search index built from metadata
- derived filter lists (genres, year buckets)
- optional joins (for example links/poster lookup tables)

### `st.session_state` (interactive state)
Use for:
- selected mode
- filters and seed selections
- last request/response context
- debug toggle and timing visibility

### Important boundary rule
Do not place large, user-specific recommendation outputs in unbounded caches by default. Cache reusable artifacts and deterministic helpers first; compute request-specific rankings on demand.

## Error Handling and Reliability Strategy
The app should treat edge-case handling as part of the product, not only backend exception handling.

### Required user-visible edge cases
- no matching movie search
- insufficient preferences for personalization
- missing metadata fields for some results
- empty recommendation set after filters
- missing artifact/setup issue

### Response strategy
- provide a clear status message
- provide fallback output when appropriate
- avoid silent failures or empty screens
- keep explanation text honest (do not claim strong personalization when fallback was used)

## Testing Strategy by Layer
A professional structure is only useful if each layer has tests that match its responsibility.

### Unit tests (`tests/unit/`)
Focus on pure logic and contracts:
- routing service mode decisions
- fallback escalation rules
- explanation formatting
- filter service behavior and controlled relaxation
- startup validator checks (with small fixtures/mocks)

### Integration tests (`tests/integration/`)
Focus on component collaboration:
- artifact loading and repository initialization from fixture artifacts
- recommendation service request -> response pipeline
- facade integration (`src/serving/api.py`) with repositories and rankers

### Smoke tests (`tests/smoke/`)
Focus on app-level startup contract:
- app starts when required artifacts exist
- app fails clearly when required artifacts are missing
- core route calls return structured responses for representative requests

### Manual QA / demo checklist (documented in TASKS)
Some recommender behaviors are easiest to verify manually in the UI:
- returning user flow
- new user/cold-start flow
- similar-movie flow
- edge-case messaging and fallback notices

## Observability and Debug Mode (Recommended)
Add a lightweight debug mode (hidden or sidebar toggle) that can display:
- selected mode and fallback status
- timing breakdown (load/validate/rank/render)
- artifact manifest/version summary
- warning messages from validation or filter relaxation

This helps developers debug the app during demos without exposing internal details to normal users.

## Current Project Assumptions (at time of writing)
These assumptions should be confirmed during implementation:
- `artifacts/` may not yet exist until the A-Phase export step is rerun.
- `streamlit_app.py` / `app/` may not exist yet (this document defines the target structure).
- dependency packaging file (`requirements.txt` or `pyproject.toml`) may not exist yet.
- A-Phase artifact manifest is a strong starting point, but a user-profile artifact should be added for returning-user mode.

## Relationship to QUAAACK Deliverables
This architecture is the implementation bridge after `K-Phase.ipynb`.
- `A-Phase.ipynb` defines the exportable artifacts and selected params.
- `C-Phase.ipynb` defines the v1 go decision and final mode behavior.
- `K-Phase.ipynb` defines the Streamlit handoff behavior, caching strategy, and edge cases.
- `TASKS.MD` (post-Task 5 additions) defines the implementation sequence that builds this architecture.

Keep those documents synchronized. If the architecture changes materially (for example switching the primary personalized engine or changing artifact contracts), update this file and the relevant tasks instead of letting the implementation drift silently.
