# TASKS.MD - QUAAACK Notebook Tasks for Movie Recommendation App

## 1. Project Context (must be stated clearly in the first notebook and referenced in all others)

### Project Type
Movie recommendation software built with **Streamlit** and developed using the **QUAAACK process**.

### Primary Stakeholders (clearly define in Q-Phase)
1. **End Users (Movie Watchers)**
   Need fast, relevant, easy-to-understand recommendations.
2. **Product Owner / Project Team**
   Need measurable recommendation quality and a usable Streamlit app.
3. **Data/ML Developer (you / team)**
   Need reproducible experiments, clear metrics, and maintainable pipelines.
4. **Non-Technical Reviewers (teachers, stakeholders, demo audience)**
   Need plain-language explanations of charts, decisions, and outcomes.

### Data Used (from `ml-25m`)
Use and document these files explicitly:
- `ml-25m/ratings.csv` (core user-item interactions)
- `ml-25m/movies.csv` (movie metadata: title, genres)
- `ml-25m/tags.csv` (user-provided tags; optional but valuable for content signals)
- `ml-25m/links.csv` (external IDs; useful for posters/metadata extensions later)
- `ml-25m/genome-scores.csv` (fine-grained tag relevance, advanced content features)
- `ml-25m/genome-tags.csv` (lookup table for genome tags)
- `ml-25m/README.txt` (dataset documentation; summarize key limits)

### Project Goals (define in Q-Phase and track through C-Phase)
1. Build a **movie recommender** that supports:
   - personalized recommendations (for users with history)
   - cold-start recommendations (for new users)
   - similar-movie recommendations (item-to-item)
2. Deliver a **Streamlit app** with clear explanations:
   - "Because you liked X"
   - "Popular in genre Y"
   - "Similar to Z"
3. Evaluate models with **ranking metrics** (not only error metrics):
   - `Precision@K`, `Recall@K`, `NDCG@K`, `HitRate@K`
   - coverage and basic diversity checks
4. Keep the solution **explainable and reproducible**.

---

## 2. Notebook Writing Standards (follow style from `.tests` repo)

These standards apply to **every notebook task below**.

### Structure and Tone
- Start with a short narrative introduction:
  - what this phase is
  - why it matters for the project
  - what the reader will understand after reading it
- Use clear section headings and subheadings.
- Write for mixed audiences:
  - technical readers (methods, metrics, code)
  - non-technical readers (plain-language explanation)
- Prefer natural-language paragraphs over bullet-heavy writing.
- Use bullet points only when they are truly needed to improve clarity (e.g., short checklists, explicit comparisons, or required itemized lists); avoid "bullet dumps."
- End with a summary / interpretation section tied to the app.

### Required "Plain Language" Explanations
- Before or after each important technical step, add a short plain-language explanation.
- Explain key ML terms (e.g., collaborative filtering, sparse matrix, NDCG) in simple words.
- Every chart/table must include:
  - what it shows
  - why it matters for the recommender app

### Diagram Rule (important)
If you include a diagram (workflow, architecture, model comparison, user flow, etc.):
- Add a short explanation paragraph for non-technical readers directly below it.
- Explain the meaning of arrows/boxes/colors in plain language.
- State what decision the diagram supports.

### Documentation Quality
- Clearly name data sources and file paths (use `ml-25m/...` paths).
- State assumptions and limitations.
- State what is placeholder, what is final, and what still needs work.
- Use consistent notebook filenames and phase names.

---

## 3. QUAAACK Task List (Notebook Deliverables)

The tasks below follow your requirement:
- `Q` and `U` are separate tasks
- `AAA` is combined into a single task
- `C` and `K` are included to complete QUAAACK

### Task 1 - Q-Phase Notebook (`Q-Phase.ipynb`) DONE

### Goal
Define the recommendation problem clearly before building anything.

### Notebook Deliverable
Create `Q-Phase.ipynb` for the movie recommendation app.

### Must Include
1. **Project overview (plain language)**
   - What the app does
   - Why recommendations are useful
   - Why Streamlit is used
2. **Stakeholders**
   - End users
   - Product owner / reviewer
   - Developer / ML engineer
   - Non-technical readers
   - For each stakeholder: needs, pain points, success criteria
3. **Core recommendation questions**
   - How do we recommend for users with history?
   - How do we recommend for new users?
   - How do we explain recommendations clearly?
4. **Scope and non-scope**
   - In scope: offline recommendations, Streamlit demo, explainability
   - Out of scope (initial version): online learning, real-time retraining, production API scaling
5. **Success metrics (business + ML)**
   - `Precision@10`, `Recall@10`, `NDCG@10`, `HitRate@10`
   - catalog coverage
   - app response target (e.g., recommendation generation under a few seconds after selection)
6. **Risks and constraints**
   - cold-start
   - popularity bias
   - sparse ratings
   - limited metadata (compared to commercial systems)
7. **QUAAACK roadmap preview**
   - one short section explaining what happens in U, AAA, C, K

### Recommended Visuals / Diagrams
- User journey diagram (input -> recommender -> top-N list -> explanation)
- QUAAACK phase roadmap

### Non-Technical Explanation Requirement
Add a short explanation below each diagram describing:
- what the boxes mean
- what happens first/next
- how this helps a movie watcher

---

### Task 2 - U-Phase Notebook (`U-Phase.ipynb`) DONE

### Goal
Understand the `ml-25m` dataset structure, quality, sparsity, and modeling constraints.

### Notebook Deliverable
Create `U-Phase.ipynb` focused on EDA and data understanding for movie recommendations.

### Must Include
1. **Dataset inventory (`ml-25m`)**
   - Describe each file and whether it is required or optional in v1
   - Summarize `ml-25m/README.txt` key points
2. **Data loading and schema inspection**
   - column names
   - dtypes
   - row counts
   - memory considerations (especially `ratings.csv`, `genome-scores.csv`)
3. **Data quality checks**
   - duplicates
   - missing values
   - invalid ratings
   - timestamp parsing
   - malformed genres or tags
4. **Exploratory analysis (core recommender insights)**
   - ratings distribution
   - users per number of ratings (activity distribution)
   - movies per number of ratings (long-tail popularity)
   - average rating per movie / user
   - time trends (rating activity over years)
   - genre frequency and co-occurrence (from `movies.csv`)
5. **Sparsity and cold-start analysis**
   - user-item matrix sparsity estimate
   - proportion of low-activity users
   - proportion of low-interaction movies
   - implications for collaborative filtering
6. **Feature availability assessment**
   - what can support content-based methods (genres, tags, genome features)
   - what can support collaborative filtering (ratings + timestamps)
7. **Train/validation/test split strategy**
   - chronological split rationale
   - why random split can mislead in recommender systems
   - leakage risks to avoid
8. **U-Phase summary**
   - which files/features move to modeling (AAA)
   - what is postponed for performance reasons (e.g., full genome usage in v1)

### Recommended Visuals / Diagrams
- Ratings histogram
- User activity histogram
- Movie popularity long-tail plot
- Timeline plot of rating counts by year
- Simple data pipeline diagram (`ml-25m` files -> processed tables)

### Non-Technical Explanation Requirement
For each chart:
- one paragraph explaining what the chart means in everyday language
- one sentence explaining how it affects recommendation quality or app UX

---

### Task 3 - AAA-Phase Notebook (`A-Phase.ipynb` or `AAA-Phase.ipynb`)

### Goal
Combine **A1 (Algorithm Selection)**, **A2 (Adapt Features)**, and **A3 (Adjust/Assess)** in one notebook and build the first working recommendation models.

### Notebook Deliverable
Create one combined notebook for model development and evaluation.

### Must Include

#### A1 - Algorithm Selection
1. **Baseline methods (required)**
   - random baseline (for sanity check)
   - popularity baseline (global top-rated/top-rated-with-min-count)
   - genre-filtered popularity baseline
2. **Candidate recommender approaches**
   - content-based (genres/tags/genome)
   - collaborative filtering (user-user, item-item, or matrix factorization)
   - hybrid recommendation (recommended final direction for app)
3. **Model selection rationale**
   - explain tradeoffs: quality, speed, explainability, implementation complexity
   - explicitly state which approach is best for the Streamlit v1 app

#### A2 - Adapt Features
4. **Feature engineering / preprocessing**
   - encode genres
   - tag preprocessing (optional in v1, required if used)
   - rating normalization strategy (if applicable)
   - minimum interaction thresholds (users/items)
   - candidate generation rules
5. **Cold-start strategy**
   - new user: genre preferences + popularity fallback
   - new item: metadata-based similarity or exclude until enough interactions
6. **Data split implementation**
   - chronological split for evaluation
   - holdout logic for top-N recommendation testing
   - leakage checks (must be documented)

#### A3 - Adjust and Assess
7. **Hyperparameter tuning**
   - choose a small, justified search space
   - tune for ranking metrics (not RMSE-only)
8. **Evaluation**
   - report `Precision@K`, `Recall@K`, `NDCG@K`, `HitRate@K`
   - compare all candidates in a summary table
   - evaluate by user segments (low activity vs high activity)
9. **Explainability examples**
   - show sample recommendations with "why" text
   - at least 2-3 user examples and 2 similar-movie examples
10. **Export plan for Streamlit**
   - what artifacts are saved (model, encoders, similarity matrix, metadata)
   - artifact paths and formats

### Recommended Visuals / Diagrams
- Model comparison table/plot (ranking metrics)
- Hybrid recommender architecture diagram
- Offline evaluation flow diagram (train -> validate -> test -> metrics)
- Example recommendation explanation cards/screenshots (if available)

### Non-Technical Explanation Requirement
Below each model comparison chart/table:
- explain which model is "better" in plain terms
- explain why a slightly lower score may still be preferred (e.g., faster and clearer)

---

### Task 4 - C-Phase Notebook (`C-Phase.ipynb`)

### Goal
Conclude, compare, and formally choose the model setup for the Streamlit app.

### Notebook Deliverable
Create `C-Phase.ipynb` as the final decision notebook.

### Must Include
1. **Final comparison summary**
   - baselines vs chosen model
   - key ranking metrics at chosen `K`
   - runtime / inference tradeoff
2. **Stakeholder-oriented interpretation**
   - what the results mean for end users
   - what they mean for project reviewers
   - what they mean for implementation complexity
3. **Failure modes and limitations**
   - sparse users
   - niche content
   - popularity dominance
   - metadata limitations in `ml-25m`
4. **Go / No-Go decision for Streamlit integration**
   - selected v1 model setup
   - deferred improvements for v2
5. **Final recommended app behavior**
   - personalized mode
   - cold-start mode
   - similar-movie mode
   - fallback behavior

### Recommended Visuals / Diagrams
- Decision matrix (quality vs speed vs explainability)
- Final system behavior flow (user input -> recommendation mode -> output)

### Non-Technical Explanation Requirement
Add a plain-language "What this means in practice" section after the decision matrix.

---

### Task 5 - K-Phase Notebook (`K-Phase.ipynb`)

### Goal
Transfer knowledge into implementation-ready guidance for the Streamlit app.

### Notebook Deliverable
Create `K-Phase.ipynb` that documents how the selected recommender is integrated into Streamlit.

### Must Include
1. **Streamlit app concept**
   - user flows (new user vs returning user vs similar-movie search)
   - screens/components (search, filters, recommendation list, explanation panel)
2. **Inference pipeline for the app**
   - load artifacts
   - preprocess user input
   - generate candidates
   - rank and explain
   - display top-N results
3. **Caching and performance strategy**
   - what to cache in Streamlit
   - what is precomputed offline
   - expected bottlenecks
4. **Error handling / edge cases**
   - no matching movie search
   - insufficient user preferences
   - missing metadata
   - empty recommendation set
5. **Plain-language demo script**
   - a short step-by-step walkthrough for non-technical stakeholders
6. **Handover checklist**
   - files needed
   - run command(s)
   - assumptions
   - known limitations

### Recommended Visuals / Diagrams
- Streamlit UI wireframe
- Request-to-result inference flow
- Artifact map (`artifacts/` + metadata + app inputs)

### Non-Technical Explanation Requirement
For each UI/inference diagram, add a short paragraph that explains:
- what the user clicks/selects
- what the app does behind the scenes
- what appears on screen and why

---

## 4. Cross-Task Standards (applies to all notebooks)

### Naming and Consistency
- Use consistent phase names:
  - `Q-Phase.ipynb`
  - `U-Phase.ipynb`
  - `A-Phase.ipynb` (combined AAA)
  - `C-Phase.ipynb`
  - `K-Phase.ipynb`
- Refer to the app consistently as the **Movie Recommendation App** (or your final product name).

### Reproducibility
- Fix random seeds where randomness exists.
- State package versions (or link to `requirements.txt` when available).
- Use explicit file paths from `ml-25m/`.
- Do not hide critical preprocessing in untracked ad-hoc scripts without documentation.

### Accessibility for Non-Technical Readers
- Avoid unexplained jargon.
- Add "Simple explanation" callouts for complex concepts.
- Connect every technical result back to a user-facing app impact.

---

## 5. Suggested Execution Order
1. `Q-Phase.ipynb`
2. `U-Phase.ipynb`
3. `A-Phase.ipynb` (AAA combined)
4. `C-Phase.ipynb`
5. `K-Phase.ipynb`

This order preserves the QUAAACK logic and matches the writing style pattern used in the `.tests` reference repo.

---

## 6. App Architecture Standards (applies to Streamlit app implementation tasks)

These standards apply to the **post-QUAAACK app implementation tasks** below and should be read together with `.ai/AGENTS.md`, `DATA.md`, `DECISIONS.md`, and `ARCHITECTURE.md`.

### Architecture Direction (required)
- Use a layered app structure with clear separation of concerns:
  - `UI/View -> Application Services -> Repositories/Infrastructure -> Artifacts`
- Keep Streamlit UI code focused on interaction and rendering.
- Keep recommendation logic, routing, and explanation generation in service-layer code (not in views).
- Keep artifact loading, file parsing, and schema validation in infrastructure/repository code (not in UI).

### Dependency Rules (required)
- `app/` may depend on `src/serving/` or application service facades, but should not parse artifact files directly.
- `src/application/` may depend on `src/domain/` and `src/application/ports/`, but not on Streamlit UI modules.
- `src/infrastructure/` may implement repository/ranker ports and read `artifacts/`, but should not import `app/views`.
- `src/domain/` should remain framework-light and reusable (requests, responses, enums, models).
- Streamlit-specific caching (`st.cache_data`, `st.cache_resource`) should be isolated in UI bootstrap or dedicated cache wrappers.

### App Runtime Rules (required)
- Do not retrain heavy models or rebuild large similarity matrices in the Streamlit request path.
- Load artifacts from `artifacts/` and run inference/ranking only.
- Validate required artifacts at startup and fail with clear, actionable error messages if files are missing.
- Provide explicit fallback behavior for sparse/new-user states and empty recommendation sets.
- Surface explanation text for each recommendation mode in plain language.

### App Quality and Trust Rules (required)
- Log or expose lightweight timing/debug information for recommendation requests (at least in a debug mode).
- Keep mode routing and fallback decisions inspectable (for example: mode used, fallback triggered, why).
- Handle missing metadata gracefully (show placeholders instead of dropping recommendations silently).
- Keep assumptions and limitations visible in docs and demo guidance.

---

## 7. Post-QUAAACK Streamlit App Implementation Tasks

The tasks below continue after `K-Phase.ipynb` and convert the notebook decisions into a working Streamlit application. They are implementation tasks (not notebook tasks), but they follow the same documentation discipline used in QUAAACK.

### Task 6 - App Architecture and Serving Contract (`ARCHITECTURE.md`)

### Goal
Define a professional, implementation-ready architecture for the Streamlit app with clear layer boundaries and dependency rules.

### Deliverable
Create `ARCHITECTURE.md` that documents the app structure, request flow, artifact/runtime separation, and layer responsibilities for the Movie Recommendation App.

### Must Include
1. **Layered application structure**
   - `UI/View -> Application Services -> Repositories/Infrastructure -> Artifacts`
   - concrete folder/file structure (for example `app/`, `src/domain/`, `src/application/`, `src/infrastructure/`, `src/serving/`)
2. **Dependency direction rules**
   - what each layer may import/call
   - what each layer must not depend on
3. **Request flow definition**
   - `View -> Controller -> RecommendationService -> RoutingService -> Ranker(s) + Repositories -> Response DTO -> Presenter -> View`
4. **Artifact/runtime boundary**
   - offline export vs app runtime loading
   - startup validation behavior and missing-artifact handling
5. **Mode routing and fallback design**
   - personalized mode
   - cold-start mode
   - similar-movie mode
   - fallback behavior and explanation routing
6. **Caching boundaries**
   - `st.cache_resource`, `st.cache_data`, and `st.session_state` usage boundaries
7. **Testing strategy by layer**
   - unit, integration, and smoke-test responsibilities
8. **Required implementation assumption**
   - include a recommended compact user-profile artifact (for example `artifacts/user_profiles_train.parquet`) for returning-user mode

### Recommended Visuals / Diagrams
- Layered architecture diagram (UI -> services -> repositories -> artifacts)
- Request-to-result sequence/flow diagram
- Artifact/runtime boundary diagram

### Non-Technical Explanation Requirement
For each architecture or flow diagram, add a short paragraph that explains:
- what each layer/box does in plain language
- what happens first/next when a user requests recommendations
- why this separation improves reliability and maintainability

---

### Task 7 - Artifact Export and Startup Validation for App Serving DONE

### Goal
Prepare and validate the offline artifacts required by the Streamlit app so the runtime path stays fast and reproducible.

### Deliverable
Export the required app-serving artifacts into `artifacts/`, define/validate a serving manifest, and implement startup validation checks for file presence and schema compatibility.

### Must Include
1. **Artifact export execution**
   - export the A-Phase planned artifacts into `artifacts/`
   - verify exported paths match the documented artifact manifest
2. **Returning-user support artifact**
   - add a compact user-profile artifact (for example `artifacts/user_profiles_train.parquet`, `.csv`, or `.jsonl`)
   - document its schema and how it is used by personalized mode
3. **Manifest and compatibility checks**
   - validate `artifacts/aaa_artifact_manifest.json`
   - validate `artifacts/aaa_selected_params.json`
   - check version/parameter compatibility with app expectations
4. **Startup validation behavior**
   - missing file detection
   - schema/column mismatch handling
   - clear error messages for developers
5. **Provenance and assumptions**
   - record which A-Phase run/config generated the artifacts
   - note sampled-vs-full evaluation assumptions when relevant

### Recommended Visuals / Diagrams
- Artifact map (`artifacts/` files and how each is used at runtime)
- Startup validation flow (load -> check -> fail fast / proceed)

### Non-Technical Explanation Requirement
For each artifact/validation diagram, explain:
- what files the app needs before it can run
- what the app checks at startup
- what happens on screen or in logs if something is missing

---

### Task 8 - Streamlit App Scaffolding and UI Foundation DONE

### Goal
Create the Streamlit app skeleton with a professional structure for views, components, controllers, presenters, and session state management.

### Deliverable
Implement the app entrypoint (`streamlit_app.py` and/or `app/main.py`) and a minimal but functional UI foundation that supports mode selection, shared filters, and structured rendering placeholders.

### Must Include
1. **App entrypoint and bootstrap**
   - `streamlit_app.py` (or root delegator to `app/main.py`)
   - app startup wiring and dependency initialization
2. **UI structure**
   - `app/views/`, `app/components/`, `app/controllers/`, `app/presenters/`, `app/state/`
   - clear responsibility split between layout/rendering and backend calls
3. **Core screens/components**
   - mode selector
   - search / selection controls
   - shared filters
   - results area and explanation/status region
4. **Session state helpers**
   - preserve selected mode, filters, and last request/response context across reruns
5. **Path/config handling**
   - central config for artifact paths and runtime settings (do not hardcode everywhere)

### Recommended Visuals / Diagrams
- Streamlit UI wireframe (sidebar + main panel)
- Component map (which UI parts render which responsibilities)

### Non-Technical Explanation Requirement
For each UI diagram/wireframe, add a short paragraph that explains:
- what the user clicks/selects
- what appears on screen
- how the layout helps users move between recommendation modes

---

### Task 9 - Repositories, Loaders, and Artifact Access Layer DONE

### Goal
Implement a repository/infrastructure layer that centralizes artifact loading, parsing, lookup construction, and startup validation so UI and services do not read files directly.

### Deliverable
Create `src/infrastructure/loaders/` and `src/infrastructure/repositories/` modules (plus ports/interfaces) for metadata, popularity tables, similarity assets, and user-profile data.

### Must Include
1. **Artifact loader module**
   - load CSV/JSON/NPZ/NPY artifacts from `artifacts/`
   - centralize file parsing and error handling
2. **Startup validator**
   - required file checks
   - schema/shape validation
   - manifest/parameter consistency checks
3. **Repository implementations**
   - movie metadata repository
   - global popularity repository
   - genre popularity repository
   - similarity repository (content + collaborative assets)
   - user profile repository
   - artifact manifest repository
4. **Application ports/interfaces**
   - define repository contracts in `src/application/ports/`
   - avoid leaking file-format details into service code
5. **Lookup construction**
   - title search indexes / normalized title lookup
   - `movieId` mapping helpers
   - reusable metadata lookups for rendering and filtering

### Recommended Visuals / Diagrams
- Repository dependency diagram (services -> ports -> infrastructure implementations)
- Artifact loading and validation sequence diagram

### Non-Technical Explanation Requirement
Explain, in plain language, why the app should load files in one place instead of in each screen or button handler.

---

### Task 10 - Application Services, Routing, and Recommendation Orchestration DONE

### Goal
Implement the application service layer that translates UI requests into recommendation results with explicit mode routing, fallback logic, and explanation generation.

### Deliverable
Create `src/application/services/` and a thin `src/serving/api.py` facade that the Streamlit UI can call for all recommendation requests.

### Must Include
1. **Recommendation orchestration service**
   - request validation handoff
   - candidate generation orchestration
   - ranking/explanation/post-filter orchestration
2. **Routing service**
   - personalized mode
   - cold-start mode
   - similar-movie mode
   - fallback escalation logic and mode trace
3. **Explanation service**
   - plain-language reasons (for example "Because you liked X", "Popular in genre Y", "Similar to Z")
   - clear fallback explanation text when personalization is weak
4. **Search and filter services**
   - title lookup / disambiguation support
   - post-ranking filters and controlled relaxation behavior
5. **Request/response DTOs**
   - typed request and response models in `src/domain/`
   - fields for status messages, warnings, mode used, and fallback reason

### Recommended Visuals / Diagrams
- Request routing flow (mode decision + fallback branches)
- Explanation generation flow (source reason -> formatted message)

### Non-Technical Explanation Requirement
Below each routing or explanation diagram, explain:
- how the app chooses the recommendation mode
- when fallback is used
- how the app tells the user what happened

---

### Task 11 - UI Integration with Service Facade and Result Rendering DONE

### Goal
Connect the Streamlit UI to the serving/application layer so the app can render real recommendations, explanations, and status messages with thin view logic.

### Deliverable
Integrate `app/views/` and `app/components/` with `src/serving/api.py` (or equivalent facade) and render end-to-end recommendations for all supported modes.

### Must Include
1. **UI-to-service integration**
   - convert widget state into request DTOs
   - call service facade from controller code (not directly from presentation-only components)
2. **Recommendation result rendering**
   - title/year/genres display
   - explanation text
   - optional poster placeholder support
3. **Mode-specific status messaging**
   - indicate which mode ran
   - indicate whether fallback was used and why
4. **Empty and error states**
   - no title match
   - insufficient preferences
   - missing metadata
   - empty recommendation set after filters
5. **View thinness rule**
   - avoid moving ranking or file-loading logic into Streamlit views/components

### Recommended Visuals / Diagrams
- UI render flow (user action -> request -> response -> cards/messages)
- Example result card / explanation layout sketch

### Non-Technical Explanation Requirement
For each UI flow or mockup diagram, explain what the user sees, why the explanation text is shown, and how fallback behavior is communicated.

---

### Task 12 - Caching, Performance, and Runtime Observability DONE

### Goal
Make the Streamlit app responsive and inspectable by applying caching correctly, bounding candidate/ranking work, and instrumenting request timings.

### Deliverable
Implement caching and timing instrumentation for startup and request-time stages, then document/verify expected responsiveness for common interactions.

### Must Include
1. **Caching implementation**
   - `st.cache_resource` for heavy immutable artifacts/resources
   - `st.cache_data` for deterministic derived tables/lookups
   - `st.session_state` for UI state
2. **Runtime boundaries**
   - artifact load once vs request-time ranking
   - avoid repeated expensive parsing on widget reruns
3. **Performance instrumentation**
   - startup load timing
   - request validation timing
   - candidate generation / ranking / rendering timing
   - total response timing
4. **Bottleneck controls**
   - candidate limits / ranking caps
   - debug mode timing output
   - safe defaults for interactive use
5. **Responsiveness checks**
   - verify common interactions feel immediate after artifacts are loaded
   - document deviations and causes

### Recommended Visuals / Diagrams
- Cache boundary diagram (startup vs request path)
- Timing breakdown chart/table for common interaction types

### Non-Technical Explanation Requirement
Below each caching or timing visual, explain:
- what is loaded once vs repeated on each click
- why caching helps the app feel responsive
- what the timing numbers mean for users (not only developers)

---

### Task 13 - Testing, QA, and Demo Readiness

### Goal
Validate that the app behavior is correct, stable, and explainable across modes, edge cases, and artifact states before demo/handover.

### Deliverable
Create tests and QA checklists that cover service logic, artifact loading, startup validation, and key end-to-end app flows for the Streamlit v1 demo.

### Must Include
1. **Unit tests**
   - routing service
   - explanation service
   - filter service / fallback behavior
   - startup validator
2. **Integration tests**
   - artifact loading and repository initialization
   - recommendation pipeline request -> response contract
3. **Smoke checks**
   - app startup with valid artifacts
   - clear failure when required artifacts are missing
4. **Manual QA checklist**
   - returning user flow
   - new user / cold-start flow
   - similar-movie flow
   - edge cases and error states
5. **Demo readiness checklist**
   - example users/titles prepared
   - fallback behavior visible and explainable
   - timing/debug output available if needed

### Recommended Visuals / Diagrams
- Test pyramid / test-scope overview
- QA flow checklist diagram (startup -> mode checks -> edge cases -> demo run)

### Non-Technical Explanation Requirement
Add a short plain-language explanation of why testing includes both automatic tests and a manual demo checklist for a recommender app.

---

### Task 14 - Packaging, Runbook, and Implementation Handover

### Goal
Make the Streamlit app reproducible and easy for another developer to run, debug, and demo from a clean environment.

### Deliverable
Add/update project runbook and packaging/setup documentation (and missing supporting files where needed) for the Streamlit app implementation.

### Must Include
1. **Dependency management**
   - create `requirements.txt` or `pyproject.toml`
   - include Streamlit and core runtime dependencies
2. **Run commands and environment setup**
   - local setup commands
   - app run command(s)
   - artifact prerequisite checks
3. **Configuration and paths**
   - document artifact paths and overrides
   - optional `.streamlit/config.toml` setup if used
4. **Developer handover docs**
   - how to regenerate artifacts
   - how to troubleshoot missing/invalid artifacts
   - how to run tests and smoke checks
5. **Known limitations and release/demo checklist**
   - sampled AAA evaluation caveat
   - historical `ml-25m` limitations
   - remaining v2 improvements and non-scope items

### Recommended Visuals / Diagrams
- Environment/setup flow (install -> export artifacts -> run app -> test)
- Handover checklist summary table

### Non-Technical Explanation Requirement
Add a short paragraph explaining why setup/run documentation is part of product quality for stakeholder demos, not only a developer convenience.

---

## 8. Extended Execution Order (QUAAACK + App Build)
1. `Q-Phase.ipynb`
2. `U-Phase.ipynb`
3. `A-Phase.ipynb` (AAA combined)
4. `C-Phase.ipynb`
5. `K-Phase.ipynb`
6. Task 6: App architecture and serving contract (`ARCHITECTURE.md`)
7. Task 7: Artifact export and startup validation
8. Task 8: Streamlit app scaffolding and UI foundation
9. Task 9: Repositories, loaders, and artifact access layer
10. Task 10: Application services, routing, and recommendation orchestration
11. Task 11: UI integration with service facade and result rendering
12. Task 12: Caching, performance, and runtime observability
13. Task 13: Testing, QA, and demo readiness
14. Task 14: Packaging, runbook, and implementation handover

This extended order preserves the original QUAAACK notebook sequence and then adds a clear, implementation-focused path to a professional Streamlit app.
