"""Utility helpers for name normalisation and numeric parsing."""

from __future__ import annotations

import re
import unicodedata
from difflib import get_close_matches
from typing import Iterable, Optional


def slugify(value: str) -> str:
    """Return a slug-like lowercase version of ``value`` without accents."""

    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip().lower()


def find_best_match(query: str, candidates: Iterable[str]) -> Optional[str]:
    """Return the best fuzzy match from ``candidates`` for ``query``."""

    if not query:
        return None
    query_slug = slugify(query)
    candidate_map = {slugify(candidate): candidate for candidate in candidates}
    if query_slug in candidate_map:
        return candidate_map[query_slug]
    for slug, original in candidate_map.items():
        if query_slug in slug or slug in query_slug:
            return original
    matches = get_close_matches(query_slug, candidate_map.keys(), n=1, cutoff=0.5)
    if not matches:
        return None
    return candidate_map[matches[0]]


def parse_numeric(value: str) -> Optional[float]:
    """Attempt to parse ``value`` into a float if possible."""

    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    value = value.strip()
    if not value or value in {"-", "--", "N/A"}:
        return None
    value = value.replace("%", "")
    try:
        return float(value)
    except ValueError:
        return None
