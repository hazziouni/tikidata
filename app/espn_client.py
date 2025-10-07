"""Lightweight HTTP client that wraps ESPN's public soccer endpoints."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Iterable, Optional

import requests

ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer"


class ESPNError(RuntimeError):
    """Raised when ESPN returns an error payload."""


class ESPNClient:
    """HTTP wrapper around a subset of the unofficial ESPN soccer API."""

    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
                ),
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    def _get(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{ESPN_BASE_URL}/{path}"
        response = self.session.get(url, params=params, timeout=15)
        response.raise_for_status()
        data: Dict[str, Any] = response.json()
        if isinstance(data, dict) and data.get("error"):
            raise ESPNError(str(data["error"]))
        return data

    @lru_cache(maxsize=32)
    def fetch_league_teams(self, league_slug: str) -> Iterable[Dict[str, Any]]:
        data = self._get(f"{league_slug}/teams")
        return data["sports"][0]["leagues"][0]["teams"]

    @lru_cache(maxsize=128)
    def fetch_team_schedule(self, league_slug: str, team_id: str, season: int) -> Iterable[Dict[str, Any]]:
        data = self._get(f"{league_slug}/teams/{team_id}/schedule", params={"season": season})
        return data.get("events", [])

    def fetch_match_summary(self, league_slug: str, event_id: str) -> Dict[str, Any]:
        return self._get(f"{league_slug}/summary", params={"event": event_id})
