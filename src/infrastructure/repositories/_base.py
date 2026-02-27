from __future__ import annotations

import json
from typing import Any


def safe_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        if value != value:  # NaN
            return None
    except Exception:
        pass
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if value != value:  # NaN
            return None
    except Exception:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_str(value: Any, *, default: str = "") -> str:
    if value is None:
        return default
    try:
        if value != value:  # NaN
            return default
    except Exception:
        pass
    text = str(value)
    return text if text else default


def coerce_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return parsed
        return [part.strip() for part in text.split(",") if part.strip()]
    return [value]


def unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def shape_tuple(value: Any) -> tuple[int, ...] | None:
    shape = getattr(value, "shape", None)
    if shape is None:
        return None
    try:
        return tuple(int(dim) for dim in shape)
    except Exception:
        return None


def array_to_int_index(values: Any) -> dict[int, int]:
    index: dict[int, int] = {}
    if values is None:
        return index
    try:
        iterable = values.tolist() if hasattr(values, "tolist") else list(values)
    except Exception:
        return index
    for position, raw in enumerate(iterable):
        coerced = safe_int(raw)
        if coerced is None:
            continue
        index[coerced] = position
    return index

