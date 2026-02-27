# DECISIONS.md - Architecture and Process Decisions

## Purpose
This file records important project decisions so they stay explicit and traceable.

Use it like a lightweight ADR (Architecture Decision Record) log:
- what was decided
- why
- what we gain
- what we trade off

When a decision changes, add a new entry instead of silently rewriting history.

## Decision Status Values
- `accepted`
- `proposed`
- `superseded`
- `rejected`

## ADR Template (copy for future decisions)

### ADR-XXX: Short decision title
- Status: `proposed`
- Date: `YYYY-MM-DD`
- Context:
  - Why this decision is needed now.
- Decision:
  - What we are choosing.
- Consequences:
  - Benefits
  - Tradeoffs / risks
- Related files:
  - `.ai/AGENTS.md`
  - `TASKS.MD`
  - (add notebook/script paths)

---

## Current Decisions

### ADR-001: Use QUAAACK as the primary workflow
- Status: `accepted`
- Date: `2026-02-25`
- Context:
  - The project needs a clear, repeatable structure for notebooks and development.
  - The audience includes non-technical reviewers, so process transparency matters.
- Decision:
  - Use the QUAAACK process: `Q`, `U`, `AAA` (combined A1/A2/A3), `C`, `K`.
  - Implement each phase as a dedicated Jupyter notebook, with `AAA` combined into one notebook.
- Consequences:
  - Benefits:
    - Clear project progression from problem definition to app handoff.
    - Easier collaboration with agents and humans.
    - Matches the style and expectations from the reference repo in `.tests/`.
  - Tradeoffs / risks:
    - More documentation overhead than ad-hoc notebooks.
    - Requires discipline to keep notebooks synchronized with code artifacts.
- Related files:
  - `TASKS.MD`
  - `.ai/AGENTS.md`

### ADR-002: Build the UI in Streamlit and keep heavy training offline
- Status: `accepted`
- Date: `2026-02-25`
- Context:
  - Streamlit is well-suited for rapid demos and educational stakeholder presentations.
  - Recomputing training or large similarity matrices during UI interactions would be too slow.
- Decision:
  - Use Streamlit for the application interface.
  - Train models and build heavy artifacts offline (not inside request-time UI code).
  - The app only loads artifacts and runs inference/ranking.
- Consequences:
  - Benefits:
    - Responsive UI and simpler deployment behavior.
    - Cleaner separation of concerns (training vs serving).
  - Tradeoffs / risks:
    - Requires artifact versioning and compatibility checks.
    - Model updates require a retrain/export step before UI sees changes.
- Related files:
  - `.ai/AGENTS.md`
  - `TASKS.MD`
  - `DATA.md`

### ADR-003: Use `ml-25m` as the source-of-truth dataset
- Status: `accepted`
- Date: `2026-02-25`
- Context:
  - A stable, well-known recommendation dataset is needed for development and evaluation.
  - The project already contains `ml-25m`.
- Decision:
  - Use files from `ml-25m/` as the canonical dataset for v1 and notebook work.
  - Raw files remain read-only; derived outputs go to processed/artifact locations.
- Consequences:
  - Benefits:
    - Reproducible experiments and shared assumptions.
    - Well-documented data semantics.
  - Tradeoffs / risks:
    - Historical data only (not real-time).
    - Dataset behavior may not fully reflect production users.
- Related files:
  - `DATA.md`
  - `TASKS.MD`

### ADR-004: Evaluate recommenders with ranking metrics (not RMSE-only)
- Status: `accepted`
- Date: `2026-02-25`
- Context:
  - The product goal is top-N recommendation usefulness, not only rating prediction error.
  - RMSE can look good while recommendations remain poor.
- Decision:
  - Primary offline evaluation uses ranking metrics:
    - `Precision@K`
    - `Recall@K`
    - `NDCG@K`
    - `HitRate@K`
  - Include coverage and basic diversity checks as secondary metrics.
- Consequences:
  - Benefits:
    - Better alignment with user experience in the Streamlit app.
    - More meaningful comparison across recommendation strategies.
  - Tradeoffs / risks:
    - Evaluation setup is more complex than simple regression metrics.
    - Requires explicit relevance threshold and split policy documentation.
- Related files:
  - `.ai/AGENTS.md`
  - `TASKS.MD`
  - `DATA.md`

### ADR-005: Use chronological splits to reduce leakage
- Status: `accepted`
- Date: `2026-02-25`
- Context:
  - Recommender systems are sensitive to leakage if future interactions are used in train-time statistics.
  - Random splits can overestimate offline performance.
- Decision:
  - Use chronological train/validation/test splits by default (preferably per-user chronological holdout).
  - Document any exceptions and justify them explicitly.
- Consequences:
  - Benefits:
    - More realistic offline results.
    - Better consistency with real-world usage (predicting future choices from past behavior).
  - Tradeoffs / risks:
    - Lower scores than random splits (but more honest).
    - Additional handling needed for users with very few interactions.
- Related files:
  - `DATA.md`
  - `TASKS.MD`

### ADR-006: Start with simple baselines, then move to hybrid recommendations
- Status: `accepted`
- Date: `2026-02-25`
- Context:
  - The project needs explainability, fast progress, and a solid benchmark.
  - Jumping directly to complex models makes debugging and stakeholder communication harder.
- Decision:
  - Start with:
    - random baseline (sanity check)
    - popularity baseline
    - genre-filtered popularity
  - Then evaluate content-based and collaborative methods.
  - Use a hybrid strategy for the Streamlit v1 app if it improves quality while staying explainable.
- Consequences:
  - Benefits:
    - Faster iteration and clearer comparisons.
    - Easier to explain to non-technical stakeholders.
  - Tradeoffs / risks:
    - Requires multiple implementations before final model selection.
    - Hybrid logic can increase integration complexity.
- Related files:
  - `.ai/AGENTS.md`
  - `TASKS.MD`

### ADR-007: Require plain-language explanations in notebooks and diagrams
- Status: `accepted`
- Date: `2026-02-25`
- Context:
  - The notebooks will be read by non-technical stakeholders.
  - Technical outputs without explanation reduce trust and usability.
- Decision:
  - Every notebook phase includes plain-language narrative sections.
  - Every major chart/diagram includes an explanation of what it shows and why it matters.
- Consequences:
  - Benefits:
    - Better communication and review readiness.
    - Easier handoff and presentation.
  - Tradeoffs / risks:
    - More writing effort.
    - Requires discipline to keep explanations updated when experiments change.
- Related files:
  - `TASKS.MD`

### ADR-008: Defer full genome feature usage unless justified by quality gain
- Status: `accepted`
- Date: `2026-02-25`
- Context:
  - `ml-25m/genome-scores.csv` is large and can slow notebook iteration and app integration.
  - v1 goals emphasize working recommendations and explainability.
- Decision:
  - Treat genome features as optional/advanced.
  - Start with `ratings.csv` + `movies.csv`, then add `tags.csv` and genome features only if metrics or explainability improve meaningfully.
- Consequences:
  - Benefits:
    - Faster development cycle.
    - Lower memory/runtime pressure.
  - Tradeoffs / risks:
    - Content quality may plateau earlier in v1.
    - Some nuanced similarity signals may be missed initially.
- Related files:
  - `DATA.md`
  - `TASKS.MD`

---

## How to Use This File During Development
- Add a new ADR when you make a decision that changes:
  - evaluation protocol
  - model family
  - split policy
  - artifact format
  - Streamlit interaction behavior
  - data filtering thresholds
- Reference the ADR ID in notebooks and commits when relevant.
