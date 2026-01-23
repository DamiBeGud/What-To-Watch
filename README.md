# QUAAACK Movie Recommender (Q stage)

Scoping and quality framing for a scalable movie recommendation system. This repo currently captures the **Q** (Question & Quality) stage: defining the problem, hypotheses, metrics, and operational bars before building.

## Contents
- `Phase1.ipynb` – Q-stage notebook: problem statement, hypotheses, offline metrics, operational SLOs, big-data notes, stakeholders/risks, UI hooks, and a toy popularity baseline with an explainability stub.
- `docker-compose.yml` + `.docker/Dockerfile` – JupyterLab environment (Python 3.11, NumPy/Pandas/Matplotlib/Scikit-learn) exposed on port 8888 with no auth token.
- `.docs/` and `.pdf/` – course/portfolio handouts (reference only).

## Run the notebook
### Docker (recommended)
1) `docker-compose up --build`
2) Open http://localhost:8888/lab (token is empty by design).

### Local Python (if you prefer)
1) `python3 -m venv .venv && source .venv/bin/activate`
2) `pip install jupyter jupyterlab numpy pandas matplotlib scikit-learn`
3) `jupyter lab`

## What to fill in Phase1
- Hypotheses deltas: replace the `__%` placeholders with target lifts (e.g., NDCG@10 vs popularity; Precision@10 for cold start).
- Operational SLO placeholders:
  - Index build `< X minutes` – choose a bound for your hardware/refresh cadence (common targets: 10–30 minutes for a daily rebuild).
  - Memory budget `≤ Y GB` per serving instance – cap RSS for the model + ANN index + caches (typical starter range: 4–8 GB if co-locating services).
- Replace toy data in the baseline cells with real slices (e.g., MovieLens 25M) and log early results in the experiment table.

## Data & scope assumptions
- Content sources: MovieLens 25M interactions; TMDB metadata for plots/genres/crew; optional IMDb priors.
- Task: personalized top-N ranking plus similar-movie lookup; English-language focus; Streamlit UI (web + mobile browser) planned for later phases; signed-in users only.

## Next steps
- Lock SLO numbers (X, Y) and metric targets, then gate future phases against them.
- Implement stronger baselines (e.g., implicit MF/SVD, item-item CF) and ANN search for similar movies.
- Add logging hooks for implicit feedback in the upcoming Streamlit app and backfill the experiment log as you iterate.
