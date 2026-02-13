# QUAAACK Movie Recommender (Q + U stages)

Scoping and data understanding for a scalable movie recommendation system. This repo now includes:
- **Q** (Question & Quality): problem framing, hypotheses, metrics, and SLO targets.
- **U** (Understanding): dataset audit and EDA for sparsity, long-tail behavior, cold-start risk, and temporal drift.

## Contents
- `Phase1.ipynb` – Q-stage notebook: problem statement, hypotheses, offline metrics, operational SLOs, big-data notes, stakeholders/risks, UI hooks, and a toy popularity baseline with an explainability stub.
- `Phase2_U.ipynb` – U-stage notebook: data loading (MovieLens + synthetic fallback), quality checks, recommendation diagnostics, temporal analysis, cold-start profiling, and draft split/cutoff decisions for A-phase.
- `docker-compose.yml` + `.docker/Dockerfile` – JupyterLab environment (Python 3.11, NumPy/Pandas/Matplotlib/Scikit-learn) exposed on port 8888 with no auth token.
- `.docs/` and `.pdf/` – course/portfolio handouts (reference only).

## Run the notebooks
### Docker (recommended)
1) `docker-compose up --build`
2) Open http://localhost:8888/lab (token is empty by design).

### Local Python (if you prefer)
1) `python3 -m venv .venv && source .venv/bin/activate`
2) `pip install jupyter jupyterlab numpy pandas matplotlib scikit-learn`
3) `jupyter lab`

## Data placement for U phase
To run `Phase2_U.ipynb` with real data, place files at:
- `ml-25m/ratings.csv`
- `ml-25m/movies.csv`

The notebook also auto-detects these alternative folders:
- `ml-2ml/`
- `data/ml-25m/`
- `data/ml-2ml/`

If none of those paths contain both CSV files, the notebook auto-generates synthetic data so the workflow still executes.

## Phase status
- **Phase 1 / Q**: complete draft, pending final numeric placeholders (`__%`, `X`, `Y`).
- **Phase 2 / U**: implementation draft complete; includes a reflection snapshot and concrete preprocessing/split decisions.

## Next steps
- Start **A (Algorithm Selection)** using the filtered data and chronological splits defined in `Phase2_U.ipynb`.
- Benchmark popularity vs CF/content/hybrid baselines with NDCG@k, HR@k, and MAP.
- Keep experiment results and reflection notes aligned with IU portfolio phase requirements.
