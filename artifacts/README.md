# Artifacts (Task 7)

This directory holds offline-exported inputs for the Streamlit serving path.

Core A-Phase artifact contract (planned):
- `movie_metadata.csv`
- `global_popularity_train.csv`
- `genre_popularity_train.csv`
- `genre_features.npz`
- `genre_feature_columns.json`
- `cf_item_similarity.npz`
- `cf_item_ids.npy`
- `aaa_selected_params.json`
- `aaa_artifact_manifest.json`

Task 7/K-Phase addition for returning-user mode:
- `user_profiles_train.jsonl` (compact user-profile artifact; documented in `user_profiles_schema.json`)

Provenance and assumptions:
- `aaa_export_provenance.json` records the A-Phase config and sampled-vs-full assumptions.
- The default export path mirrors the A-Phase runtime-safe sampled configuration (`sample_max_users=1200`).

Validation:
- Run startup validation before launching the app:
  `python3 -m src.infrastructure.loaders.startup_validator --artifacts-dir artifacts`

Regeneration:
- Offline export (requires `numpy` + `pandas`, optional `pyarrow` only if you later switch user profiles to parquet):
  `python3 -m src.infrastructure.loaders.artifact_exporter --artifacts-dir artifacts`
