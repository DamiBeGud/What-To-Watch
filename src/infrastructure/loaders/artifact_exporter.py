from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union

from .artifact_loader import (
    A_PHASE_ARTIFACT_MANIFEST_TEMPLATE,
    PROVENANCE_FILENAME,
    RECOMMENDED_USER_PROFILE_ARTIFACT,
    REFERENCE_SELECTED_V1_PARAMS,
    USER_PROFILE_SCHEMA_DOC_FILENAME,
    write_json_file,
)
from .startup_validator import StartupValidationError, validate_startup_artifacts


class ArtifactExportError(Exception):
    """Raised when offline artifact export cannot complete."""


RATINGS_DTYPES = {
    "userId": "int32",
    "movieId": "int32",
    "rating": "float32",
    "timestamp": "int64",
}
MOVIES_DTYPES = {
    "movieId": "int32",
    "title": "string",
    "genres": "string",
}

A_PHASE_CONFIG = {
    # Mirrors the documented A-Phase notebook defaults used for the runtime-safe sampled export path.
    "seed": 42,
    "k": 10,
    "relevance_threshold": 4.0,
    "val_holdout": 1,
    "test_holdout": 1,
    "min_train_interactions_after_split": 5,
    "sample_max_users": 1200,
    "sample_user_strategy": "random_eligible",
    "max_ratings_rows": None,
    "content_profile_min_rating": 4.0,
    "content_candidate_limit_default": 1200,
    "genre_pref_top_n_default": 2,
    "pop_min_count_default": 20,
    "cf_positive_threshold": 4.0,
    "cf_min_item_interactions": 20,
    "cf_max_items": 2000,
    "cf_top_neighbors_default": 50,
    "tune_user_limit": 400,
    "segment_split_quantile": 0.5,
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _require_export_dependencies() -> tuple[Any, Any]:
    missing: list[str] = []
    try:
        import numpy as np  # type: ignore
    except ModuleNotFoundError:
        np = None  # type: ignore
        missing.append("numpy")

    try:
        import pandas as pd  # type: ignore
    except ModuleNotFoundError:
        pd = None  # type: ignore
        missing.append("pandas")

    if missing:
        install_hint = "pip install numpy pandas pyarrow"
        raise ArtifactExportError(
            "Artifact export is blocked by missing Python dependencies: "
            + ", ".join(missing)
            + ". Install them (for example: "
            + install_hint
            + ") and rerun: python3 -m src.infrastructure.loaders.artifact_exporter --artifacts-dir artifacts"
        )
    return np, pd


def _load_inputs(data_dir: Path, config: dict[str, Any], np: Any, pd: Any) -> tuple[Any, Any, Any]:
    ratings_df = pd.read_csv(data_dir / "ratings.csv", dtype=RATINGS_DTYPES)
    movies_df = pd.read_csv(data_dir / "movies.csv", dtype=MOVIES_DTYPES)

    if config.get("max_ratings_rows"):
        ratings_df = ratings_df.head(int(config["max_ratings_rows"])).copy()

    ratings_df["timestamp_dt"] = pd.to_datetime(ratings_df["timestamp"], unit="s", utc=True, errors="coerce")
    movies_df["genres"] = movies_df["genres"].fillna("(no genres listed)").astype("string")
    movies_df["year"] = (
        movies_df["title"].astype("string").str.extract(r"\((\d{4})\)\s*$", expand=False).astype("Int64")
    )
    movies_df["genre_list"] = (
        movies_df["genres"]
        .astype("string")
        .str.split(r"\|")
        .apply(lambda x: x if isinstance(x, list) else ["(no genres listed)"])
    )
    movie_meta_df = movies_df[["movieId", "title", "year", "genres"]].copy()
    movie_meta_df = movie_meta_df.drop_duplicates(subset=["movieId"]).set_index("movieId")

    return ratings_df, movies_df, movie_meta_df


def _build_chronological_split(ratings: Any, movies_df: Any, config: dict[str, Any], np: Any) -> dict[str, Any]:
    rel_threshold = float(config["relevance_threshold"])
    val_holdout = int(config["val_holdout"])
    test_holdout = int(config["test_holdout"])
    min_train_after_split = int(config["min_train_interactions_after_split"])
    min_total_needed = val_holdout + test_holdout + min_train_after_split

    ratings = ratings.dropna(subset=["timestamp_dt"]).copy()
    ratings = ratings[ratings["movieId"].isin(movies_df["movieId"])].copy()

    user_total_counts = ratings.groupby("userId").size().rename("total_interactions")
    eligible_users = user_total_counts[user_total_counts >= min_total_needed].index.to_numpy()

    rng = np.random.default_rng(int(config["seed"]))
    if config.get("sample_max_users") is not None and len(eligible_users) > int(config["sample_max_users"]):
        sampled_users = rng.choice(eligible_users, size=int(config["sample_max_users"]), replace=False)
    else:
        sampled_users = eligible_users

    sampled_users = np.sort(sampled_users)
    ratings_work = ratings[ratings["userId"].isin(sampled_users)].copy()
    ratings_work = ratings_work.sort_values(["userId", "timestamp", "movieId"]).reset_index(drop=True)

    ratings_work["pos_asc"] = ratings_work.groupby("userId").cumcount()
    ratings_work["n_user"] = ratings_work.groupby("userId")["movieId"].transform("size").astype("int32")
    ratings_work["pos_desc"] = (ratings_work["n_user"] - 1 - ratings_work["pos_asc"]).astype("int32")

    test_mask = ratings_work["pos_desc"] < test_holdout
    val_mask = (ratings_work["pos_desc"] >= test_holdout) & (ratings_work["pos_desc"] < (test_holdout + val_holdout))
    train_mask = ratings_work["pos_desc"] >= (test_holdout + val_holdout)

    train_df = ratings_work.loc[train_mask].copy()
    val_df = ratings_work.loc[val_mask].copy()
    test_df = ratings_work.loc[test_mask].copy()

    train_counts = train_df.groupby("userId").size().rename("train_interactions")
    valid_users = train_counts[train_counts >= min_train_after_split].index

    train_df = train_df[train_df["userId"].isin(valid_users)].copy()
    val_df = val_df[val_df["userId"].isin(valid_users)].copy()
    test_df = test_df[test_df["userId"].isin(valid_users)].copy()

    train_df["is_relevant"] = train_df["rating"] >= rel_threshold
    val_df["is_relevant"] = val_df["rating"] >= rel_threshold
    test_df["is_relevant"] = test_df["rating"] >= rel_threshold

    leakage_df = (
        train_df.groupby("userId")["timestamp"]
        .max()
        .rename("train_max_ts")
        .to_frame()
        .join(val_df.groupby("userId")["timestamp"].min().rename("val_min_ts"), how="left")
        .join(test_df.groupby("userId")["timestamp"].min().rename("test_min_ts"), how="left")
    )
    leakage_df["train_before_val"] = leakage_df["train_max_ts"] <= leakage_df["val_min_ts"]
    leakage_df["train_before_test"] = leakage_df["train_max_ts"] <= leakage_df["test_min_ts"]

    return {
        "train": train_df,
        "val": val_df,
        "test": test_df,
        "sampled_users": sampled_users,
        "eligible_user_count_before_sampling": int(len(eligible_users)),
        "min_total_needed": int(min_total_needed),
        "leakage_checks": leakage_df,
    }


def _build_popularity_table(train_df: Any, np: Any) -> Any:
    pop = (
        train_df.groupby("movieId")
        .agg(rating_count=("rating", "size"), mean_rating=("rating", "mean"))
        .reset_index()
    )
    global_mean = float(train_df["rating"].mean()) if len(train_df) else 0.0
    m = 20.0
    pop["pop_weighted_rating"] = (
        (pop["rating_count"] / (pop["rating_count"] + m)) * pop["mean_rating"]
        + (m / (pop["rating_count"] + m)) * global_mean
    )
    pop["pop_score"] = pop["pop_weighted_rating"] * np.log1p(pop["rating_count"])
    return pop.sort_values(["pop_score", "rating_count", "mean_rating"], ascending=False).reset_index(drop=True)


def _build_genre_popularity(train_df: Any, movies_df: Any, np: Any) -> Any:
    train_with_genres = train_df.merge(movies_df[["movieId", "genres"]], on="movieId", how="left")
    train_genre_long = (
        train_with_genres[["movieId", "rating", "genres"]]
        .assign(genres=lambda d: d["genres"].fillna("(no genres listed)").astype("string").str.split(r"\|"))
        .explode("genres")
        .rename(columns={"genres": "genre"})
    )
    train_genre_long["genre"] = train_genre_long["genre"].astype("string").str.strip()

    genre_popularity_df = (
        train_genre_long.groupby(["genre", "movieId"])
        .agg(rating_count=("rating", "size"), mean_rating=("rating", "mean"))
        .reset_index()
    )
    if len(genre_popularity_df):
        genre_popularity_df["genre_pop_score"] = genre_popularity_df["mean_rating"] * np.log1p(
            genre_popularity_df["rating_count"]
        )
    else:
        genre_popularity_df["genre_pop_score"] = []
    return genre_popularity_df.sort_values(
        ["genre", "genre_pop_score", "rating_count"], ascending=[True, False, False]
    ).reset_index(drop=True)


def _build_genre_features(movies_df: Any, np: Any) -> tuple[Any, Any, list[str]]:
    genre_feature_df = movies_df[["movieId"]].copy()
    genre_dummies = movies_df["genres"].str.get_dummies(sep="|").astype("float32")
    genre_feature_df = genre_feature_df.merge(genre_dummies, left_index=True, right_index=True, how="left")
    genre_feature_cols = [c for c in genre_feature_df.columns if c != "movieId"]
    genre_matrix_df = genre_feature_df.set_index("movieId")[genre_feature_cols].astype("float32")
    genre_matrix = genre_matrix_df.to_numpy(dtype=np.float32)
    genre_movie_ids = genre_matrix_df.index.to_numpy(dtype=np.int64)
    return genre_movie_ids, genre_matrix, genre_feature_cols


def _build_cf_similarity(train_df: Any, config: dict[str, Any], np: Any, pd: Any) -> tuple[Any, Any]:
    positive_threshold = float(config["cf_positive_threshold"])
    cf_positive_df = train_df[train_df["rating"] >= positive_threshold][["userId", "movieId"]].drop_duplicates()
    cf_item_counts = cf_positive_df.groupby("movieId").size().sort_values(ascending=False)
    cf_item_pool = cf_item_counts[cf_item_counts >= int(config["cf_min_item_interactions"])].index.to_list()
    if config.get("cf_max_items") is not None:
        cf_item_pool = cf_item_pool[: int(config["cf_max_items"])]

    cf_positive_pool_df = cf_positive_df[cf_positive_df["movieId"].isin(cf_item_pool)].drop_duplicates().reset_index(drop=True)
    if len(cf_positive_pool_df) == 0:
        return np.array([], dtype=np.int64), np.empty((0, 0), dtype=np.float32)

    cf_item_user_matrix_df = pd.crosstab(
        index=cf_positive_pool_df["movieId"].to_numpy(),
        columns=cf_positive_pool_df["userId"].to_numpy(),
    )
    cf_item_ids = cf_item_user_matrix_df.index.to_numpy(dtype=np.int64)
    cf_matrix = cf_item_user_matrix_df.to_numpy(dtype=np.float32)
    cf_norms = np.linalg.norm(cf_matrix, axis=1)
    denom = np.outer(cf_norms, cf_norms)
    cf_similarity = cf_matrix @ cf_matrix.T
    cf_similarity = np.divide(cf_similarity, denom, out=np.zeros_like(cf_similarity), where=denom > 0)
    np.fill_diagonal(cf_similarity, 0.0)
    return cf_item_ids, cf_similarity.astype(np.float32)


def _top_genres_for_user(movie_ids: list[int], movie_genre_list_map: dict[int, list[str]], top_n: int) -> list[str]:
    genre_counts: dict[str, float] = {}
    for movie_id in movie_ids:
        for genre in movie_genre_list_map.get(int(movie_id), []):
            if not isinstance(genre, str):
                continue
            genre_counts[genre] = genre_counts.get(genre, 0.0) + 1.0
    return [g for g, _ in sorted(genre_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]]


def _build_user_profiles_train_jsonl_rows(train_df: Any, movies_df: Any, config: dict[str, Any]) -> list[dict[str, Any]]:
    rel_threshold = float(config["relevance_threshold"])
    preferred_top_n = int(REFERENCE_SELECTED_V1_PARAMS["genre_pref_top_n"])
    movie_genre_list_map: dict[int, list[str]] = movies_df.set_index("movieId")["genre_list"].to_dict()

    train_sorted = train_df.sort_values(["userId", "timestamp", "movieId"]).copy()
    seen_by_user = train_sorted.groupby("userId")["movieId"].apply(lambda s: [int(v) for v in s.tolist()]).to_dict()

    positive_sorted = train_df[train_df["rating"] >= rel_threshold].sort_values(
        ["userId", "rating", "timestamp"], ascending=[True, False, False]
    )
    positive_by_user = (
        positive_sorted.groupby("userId")["movieId"].apply(lambda s: [int(v) for v in s.tolist()]).to_dict()
    )

    counts = train_df.groupby("userId").size().rename("train_interaction_count")
    positive_counts = (
        train_df[train_df["rating"] >= rel_threshold].groupby("userId").size().rename("positive_interaction_count")
    )
    mean_ratings = train_df.groupby("userId")["rating"].mean().rename("train_mean_rating")

    user_ids = sorted(int(u) for u in counts.index.tolist())
    rows: list[dict[str, Any]] = []
    for user_id in user_ids:
        seen_movie_ids = seen_by_user.get(user_id, [])
        positive_seed_movie_ids = positive_by_user.get(user_id, [])
        genre_seed_movies = positive_seed_movie_ids if positive_seed_movie_ids else seen_movie_ids
        preferred_genres = _top_genres_for_user(genre_seed_movies, movie_genre_list_map, top_n=preferred_top_n)
        rows.append(
            {
                "userId": int(user_id),
                "train_interaction_count": int(counts.loc[user_id]),
                "positive_interaction_count": int(positive_counts.get(user_id, 0)),
                "train_mean_rating": float(mean_ratings.loc[user_id]),
                "seen_movie_ids": seen_movie_ids,
                "positive_seed_movie_ids": positive_seed_movie_ids,
                "preferred_genres": preferred_genres,
            }
        )
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True))
            handle.write("\n")


def _build_user_profile_schema_doc() -> dict[str, Any]:
    return {
        "artifact_path": f"artifacts/{RECOMMENDED_USER_PROFILE_ARTIFACT}",
        "format": "jsonl",
        "schema_version": "1.0",
        "description": "Compact train-split user profiles for returning-user personalized mode (no runtime ratings.csv load).",
        "personalized_mode_usage": (
            "At app startup, repositories load this artifact to resolve a returning user's seen items, positive seed items, "
            "and simple preference hints (preferred genres). The app can route to hybrid personalization quickly without "
            "loading the full ml-25m/ratings.csv file in the request path."
        ),
        "required_fields": [
            {"name": "userId", "type": "int", "notes": "MovieLens user ID present in the AAA train split export scope."},
            {"name": "train_interaction_count", "type": "int", "notes": "Count of train interactions after chronological split."},
            {"name": "positive_interaction_count", "type": "int", "notes": "Count of train ratings >= relevance_threshold."},
            {"name": "train_mean_rating", "type": "float", "notes": "Mean explicit rating in the train split."},
            {"name": "seen_movie_ids", "type": "list[int]", "notes": "Chronological train history movie IDs."},
            {"name": "positive_seed_movie_ids", "type": "list[int]", "notes": "Positive train movies sorted by rating then recency."},
            {"name": "preferred_genres", "type": "list[str]", "notes": "Top genres derived from positive seeds (or seen items fallback)."},
        ],
        "tradeoff_note": (
            "JSONL is used for portability in environments without parquet dependencies. "
            "Parquet is a valid future upgrade for smaller on-disk size and faster columnar scans."
        ),
    }


def _build_provenance_doc(
    *,
    data_dir: Path,
    artifacts_dir: Path,
    split_data: dict[str, Any],
    train_df: Any,
    user_profiles_path: Path,
) -> dict[str, Any]:
    leakage_checks = split_data["leakage_checks"]
    return {
        "artifact_bundle_schema_version": "1.0",
        "generated_at_utc": _utc_now_iso(),
        "generator": "src.infrastructure.loaders.artifact_exporter",
        "source_notebook": "A-Phase.ipynb",
        "selected_params_path": "artifacts/aaa_selected_params.json",
        "artifact_manifest_path": "artifacts/aaa_artifact_manifest.json",
        "user_profiles_artifact_path": f"artifacts/{user_profiles_path.name}",
        "a_phase_config": A_PHASE_CONFIG,
        "selected_v1_reference_source": "C-Phase.ipynb",
        "selected_v1_params": REFERENCE_SELECTED_V1_PARAMS,
        "sampling_assumption": {
            "aaa_notebook_scope": "runtime-safe sampled eligible users by default",
            "sample_max_users": A_PHASE_CONFIG["sample_max_users"],
            "sample_user_strategy": A_PHASE_CONFIG["sample_user_strategy"],
            "note": (
                "This export follows the A-Phase runtime-safe sampled configuration unless the exporter config is changed. "
                "This is suitable for Streamlit v1 demo serving but should be documented as sampled-vs-full when reporting results."
            ),
        },
        "evaluation_assumptions": {
            "split_policy": "per-user chronological holdout",
            "val_holdout": A_PHASE_CONFIG["val_holdout"],
            "test_holdout": A_PHASE_CONFIG["test_holdout"],
            "min_train_interactions_after_split": A_PHASE_CONFIG["min_train_interactions_after_split"],
            "relevance_threshold": A_PHASE_CONFIG["relevance_threshold"],
            "k": A_PHASE_CONFIG["k"],
        },
        "source_data": {
            "ratings_csv": str((data_dir / "ratings.csv").as_posix()),
            "movies_csv": str((data_dir / "movies.csv").as_posix()),
        },
        "export_summary": {
            "eligible_users_before_sampling": int(split_data["eligible_user_count_before_sampling"]),
            "sampled_users_used": int(len(split_data["sampled_users"])),
            "train_rows": int(len(split_data["train"])),
            "val_rows": int(len(split_data["val"])),
            "test_rows": int(len(split_data["test"])),
            "train_users": int(train_df["userId"].nunique()),
            "train_movies": int(train_df["movieId"].nunique()),
            "leakage_check_train_before_val_pass_rate": float(leakage_checks["train_before_val"].dropna().mean()),
            "leakage_check_train_before_test_pass_rate": float(leakage_checks["train_before_test"].dropna().mean()),
        },
    }


def _build_artifacts_readme(artifacts_dir: Path, user_profiles_filename: str) -> str:
    lines = [
        "# Artifacts (Task 7)",
        "",
        "This directory holds offline-exported inputs for the Streamlit serving path.",
        "",
        "Core A-Phase artifact contract (planned):",
        "- `movie_metadata.csv`",
        "- `global_popularity_train.csv`",
        "- `genre_popularity_train.csv`",
        "- `genre_features.npz`",
        "- `genre_feature_columns.json`",
        "- `cf_item_similarity.npz`",
        "- `cf_item_ids.npy`",
        "- `aaa_selected_params.json`",
        "- `aaa_artifact_manifest.json`",
        "",
        "Task 7/K-Phase addition for returning-user mode:",
        f"- `{user_profiles_filename}` (compact user-profile artifact; documented in `{USER_PROFILE_SCHEMA_DOC_FILENAME}`)",
        "",
        "Provenance and assumptions:",
        f"- `{PROVENANCE_FILENAME}` records the A-Phase config and sampled-vs-full assumptions.",
        "- The default export path mirrors the A-Phase runtime-safe sampled configuration (`sample_max_users=1200`).",
        "",
        "Validation:",
        "- Run startup validation before launching the app:",
        "  `python3 -m src.infrastructure.loaders.startup_validator --artifacts-dir artifacts`",
        "",
        "Regeneration:",
        "- Offline export (requires `numpy` + `pandas`, optional `pyarrow` only if you later switch user profiles to parquet):",
        "  `python3 -m src.infrastructure.loaders.artifact_exporter --artifacts-dir artifacts`",
    ]
    return "\n".join(lines) + "\n"


def export_artifacts(
    *,
    data_dir: Union[str, Path] = "ml-25m",
    artifacts_dir: Union[str, Path] = "artifacts",
    validate_after_export: bool = True,
) -> dict[str, Any]:
    np, pd = _require_export_dependencies()
    data_dir_path = Path(data_dir)
    artifacts_dir_path = Path(artifacts_dir)
    artifacts_dir_path.mkdir(parents=True, exist_ok=True)

    ratings_df, movies_df, movie_meta_df = _load_inputs(data_dir_path, A_PHASE_CONFIG, np=np, pd=pd)
    split_data = _build_chronological_split(ratings_df, movies_df, A_PHASE_CONFIG, np=np)
    train_df = split_data["train"]

    popularity_table_df = _build_popularity_table(train_df, np=np)
    genre_popularity_df = _build_genre_popularity(train_df, movies_df, np=np)
    genre_movie_ids, genre_matrix, genre_feature_cols = _build_genre_features(movies_df, np=np)
    cf_item_ids, cf_similarity = _build_cf_similarity(train_df, A_PHASE_CONFIG, np=np, pd=pd)
    user_profile_rows = _build_user_profiles_train_jsonl_rows(train_df, movies_df, A_PHASE_CONFIG)

    # Core A-Phase artifacts
    movie_meta_df.reset_index().to_csv(artifacts_dir_path / "movie_metadata.csv", index=False)
    popularity_table_df.to_csv(artifacts_dir_path / "global_popularity_train.csv", index=False)
    genre_popularity_df.to_csv(artifacts_dir_path / "genre_popularity_train.csv", index=False)

    np.savez_compressed(
        artifacts_dir_path / "genre_features.npz",
        movie_ids=genre_movie_ids.astype(np.int64),
        genre_matrix=genre_matrix.astype(np.float32),
    )
    (artifacts_dir_path / "genre_feature_columns.json").write_text(
        json.dumps(list(genre_feature_cols), indent=2),
        encoding="utf-8",
    )
    np.savez_compressed(
        artifacts_dir_path / "cf_item_similarity.npz",
        similarity=cf_similarity.astype(np.float32),
    )
    np.save(artifacts_dir_path / "cf_item_ids.npy", cf_item_ids.astype(np.int64))

    # Contract files
    write_json_file(artifacts_dir_path / "aaa_selected_params.json", REFERENCE_SELECTED_V1_PARAMS)
    write_json_file(artifacts_dir_path / "aaa_artifact_manifest.json", A_PHASE_ARTIFACT_MANIFEST_TEMPLATE)

    # Task 7 returning-user support artifact + documentation
    user_profiles_path = artifacts_dir_path / RECOMMENDED_USER_PROFILE_ARTIFACT
    _write_jsonl(user_profiles_path, user_profile_rows)
    write_json_file(artifacts_dir_path / USER_PROFILE_SCHEMA_DOC_FILENAME, _build_user_profile_schema_doc())

    provenance = _build_provenance_doc(
        data_dir=data_dir_path,
        artifacts_dir=artifacts_dir_path,
        split_data=split_data,
        train_df=train_df,
        user_profiles_path=user_profiles_path,
    )
    write_json_file(artifacts_dir_path / PROVENANCE_FILENAME, provenance)
    (artifacts_dir_path / "README.md").write_text(
        _build_artifacts_readme(artifacts_dir_path, user_profiles_path.name),
        encoding="utf-8",
    )

    validation_report = None
    if validate_after_export:
        try:
            validation_report = validate_startup_artifacts(artifacts_dir_path, require_user_profiles=True)
        except StartupValidationError as exc:
            raise ArtifactExportError(
                "Artifacts were written, but startup validation failed immediately after export.\n" + str(exc)
            ) from exc

    return {
        "artifacts_dir": str(artifacts_dir_path.resolve()),
        "user_profiles_path": str(user_profiles_path.resolve()),
        "rows": {
            "movie_metadata": int(len(movie_meta_df)),
            "global_popularity": int(len(popularity_table_df)),
            "genre_popularity": int(len(genre_popularity_df)),
            "user_profiles": int(len(user_profile_rows)),
            "cf_item_ids": int(len(cf_item_ids)),
        },
        "validation_report": None if validation_report is None else validation_report.to_dict(),
    }


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export A-Phase-compatible serving artifacts for Streamlit v1.")
    parser.add_argument("--data-dir", default="ml-25m", help="Path to the MovieLens data directory (default: ml-25m)")
    parser.add_argument("--artifacts-dir", default="artifacts", help="Output artifact directory (default: artifacts)")
    parser.add_argument("--skip-validation", action="store_true", help="Skip startup validation after export")
    parser.add_argument("--json", action="store_true", help="Print export result as JSON")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        result = export_artifacts(
            data_dir=args.data_dir,
            artifacts_dir=args.artifacts_dir,
            validate_after_export=not args.skip_validation,
        )
    except ArtifactExportError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive top-level error formatting.
        print(f"Unexpected export failure: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Artifacts exported to {result['artifacts_dir']}")
        print(f"- user profiles: {result['user_profiles_path']}")
        for name, count in result["rows"].items():
            print(f"- {name}: {count}")
        if result["validation_report"] is not None:
            print("- startup validation: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
