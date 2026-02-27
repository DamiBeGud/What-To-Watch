from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from src.application.ports.repositories import MovieMetadataRecord


def normalize_title(value: str) -> str:
    return str(value or "").strip().casefold()


def split_genres(genres: str) -> tuple[str, ...]:
    items = [part.strip() for part in str(genres or "").split("|") if part.strip()]
    if not items:
        return ("(no genres listed)",)
    return tuple(items)


def build_movie_label(record: MovieMetadataRecord) -> str:
    if record.year is not None:
        return f"{record.title} ({record.year}) [{record.movie_id}]"
    return f"{record.title} [{record.movie_id}]"


@dataclass(frozen=True)
class MetadataLookups:
    records_by_id: dict[int, MovieMetadataRecord]
    genres_by_movie_id: dict[int, tuple[str, ...]]
    search_rows: list[dict[str, object]]
    normalized_title_lookup: dict[str, list[dict[str, object]]]
    genre_values: list[str]
    year_min: Optional[int]
    year_max: Optional[int]


def build_metadata_lookups(records: Iterable[MovieMetadataRecord]) -> MetadataLookups:
    records_by_id: dict[int, MovieMetadataRecord] = {}
    genres_by_movie_id: dict[int, tuple[str, ...]] = {}
    search_rows: list[dict[str, object]] = []
    normalized_title_lookup: dict[str, list[dict[str, object]]] = {}
    year_values: list[int] = []
    genre_set: set[str] = set()
    saw_no_genres = False

    for record in records:
        records_by_id[record.movie_id] = record
        genres_by_movie_id[record.movie_id] = record.genres_list
        title_norm = normalize_title(record.title)
        row = {
            "movieId": record.movie_id,
            "title": record.title,
            "year": record.year,
            "genres": record.genres,
            "label": build_movie_label(record),
            "title_norm": title_norm,
        }
        search_rows.append(row)
        normalized_title_lookup.setdefault(title_norm, []).append(row)

        if record.year is not None:
            year_values.append(record.year)
        for genre in record.genres_list:
            if genre == "(no genres listed)":
                saw_no_genres = True
                continue
            genre_set.add(genre)

    search_rows.sort(key=lambda item: (str(item.get("title_norm", "")), int(item.get("movieId", 0))))
    year_min = min(year_values) if year_values else None
    year_max = max(year_values) if year_values else None

    genre_values = sorted(genre_set)
    if saw_no_genres:
        genre_values.append("(no genres listed)")

    return MetadataLookups(
        records_by_id=records_by_id,
        genres_by_movie_id=genres_by_movie_id,
        search_rows=search_rows,
        normalized_title_lookup=normalized_title_lookup,
        genre_values=genre_values,
        year_min=year_min,
        year_max=year_max,
    )

