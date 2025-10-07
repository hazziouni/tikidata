"""High level service that orchestrates the match data scraping workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from .constants import LeagueConfig, SUPPORTED_LEAGUES
from .espn_client import ESPNClient
from .utils import find_best_match, parse_numeric, slugify


class TeamLookupError(RuntimeError):
    """Raised when the given team name cannot be matched to a league entry."""


class MatchLookupError(RuntimeError):
    """Raised when no event matches the provided teams and season."""


@dataclass
class Scoreline:
    team: str
    team_id: str
    score: int
    home_away: str
    record: Optional[str]
    possession: Optional[float]


@dataclass
class MatchMetadata:
    event_id: str
    competition: str
    status: str
    start_time: datetime
    venue: Optional[str]
    attendance: Optional[str]
    officials: List[str]
    scoreline: Dict[str, Scoreline]


@dataclass
class MatchData:
    metadata: MatchMetadata
    team_stats: pd.DataFrame
    player_stats: pd.DataFrame
    key_events: pd.DataFrame


class MatchService:
    """Service responsible for fetching and transforming match analytics data."""

    def __init__(self, client: Optional[ESPNClient] = None) -> None:
        self.client = client or ESPNClient()

    def _resolve_league(self, league_name: str) -> LeagueConfig:
        if league_name in SUPPORTED_LEAGUES:
            return SUPPORTED_LEAGUES[league_name]
        league_slug = slugify(league_name)
        for config in SUPPORTED_LEAGUES.values():
            if league_slug in {slugify(config.name), *(slugify(alias) for alias in config.aliases)}:
                return config
        raise ValueError(f"Championnat non pris en charge : {league_name}")

    def _resolve_team(self, league: LeagueConfig, raw_name: str) -> Dict:
        teams = list(self.client.fetch_league_teams(league.espn_slug))
        candidate = find_best_match(raw_name, [team["team"]["displayName"] for team in teams])
        if not candidate:
            raise TeamLookupError(f"Impossible de trouver l'équipe '{raw_name}'.")
        return next(team for team in teams if team["team"]["displayName"] == candidate)

    def _season_to_year(self, season: str) -> int:
        season = season.strip()
        if "-" in season:
            start_year = season.split("-")[0]
            return int(start_year)
        return int(season)

    def _find_event(self, league: LeagueConfig, season_year: int, home_team_id: str, away_team_id: str) -> Dict:
        def _search(team_id: str) -> Optional[Dict]:
            events = self.client.fetch_team_schedule(league.espn_slug, team_id, season_year)
            for event in events:
                if event.get("league", {}).get("slug") != league.espn_slug:
                    continue
                competitors = event["competitions"][0]["competitors"]
                if self._event_matches(competitors, home_team_id, away_team_id):
                    return event
            return None

        event = _search(home_team_id) or _search(away_team_id)
        if not event:
            raise MatchLookupError("Aucun match trouvé pour ces critères.")
        return event

    @staticmethod
    def _event_matches(competitors: List[Dict], home_team_id: str, away_team_id: str) -> bool:
        seen_home = seen_away = False
        for competitor in competitors:
            team_id = str(competitor["team"]["id"])
            home_away = competitor.get("homeAway")
            if team_id == str(home_team_id) and home_away == "home":
                seen_home = True
            if team_id == str(away_team_id) and home_away == "away":
                seen_away = True
        return seen_home and seen_away

    def load_match(self, league_name: str, season: str, home_team: str, away_team: str) -> MatchData:
        league = self._resolve_league(league_name)
        home = self._resolve_team(league, home_team)
        away = self._resolve_team(league, away_team)
        season_year = self._season_to_year(season)
        event = self._find_event(league, season_year, home["team"]["id"], away["team"]["id"])
        summary = self.client.fetch_match_summary(league.espn_slug, event["id"])
        metadata = self._build_metadata(summary)
        team_stats = self._build_team_stats(summary)
        player_stats = self._build_player_stats(summary)
        key_events = self._build_key_events(summary)
        return MatchData(metadata=metadata, team_stats=team_stats, player_stats=player_stats, key_events=key_events)

    def _build_metadata(self, summary: Dict) -> MatchMetadata:
        competition = summary["header"]["competitions"][0]
        scoreline: Dict[str, Scoreline] = {}
        for competitor in competition["competitors"]:
            record = None
            if competitor.get("record"):
                record = ", ".join(r.get("summary", "") for r in competitor["record"])
            possession = None
            if competitor.get("possession") and competitor["possession"].get("displayValue"):
                possession = parse_numeric(str(competitor["possession"]["displayValue"]))
            scoreline[competitor["homeAway"]] = Scoreline(
                team=competitor["team"]["displayName"],
                team_id=str(competitor["team"]["id"]),
                score=int(competitor.get("score", 0)),
                home_away=competitor.get("homeAway", ""),
                record=record,
                possession=possession,
            )
        start_time = datetime.fromisoformat(competition["date"].replace("Z", "+00:00"))
        officials = [official.get("displayName") for official in competition.get("officials", []) if official.get("displayName")]
        attendance = competition.get("attendance")
        return MatchMetadata(
            event_id=str(competition["id"]),
            competition=competition.get("league", {}).get("name", ""),
            status=competition.get("status", {}).get("type", {}).get("description", ""),
            start_time=start_time,
            venue=competition.get("venue", {}).get("fullName"),
            attendance=attendance,
            officials=officials,
            scoreline=scoreline,
        )

    def _build_team_stats(self, summary: Dict) -> pd.DataFrame:
        records: List[Dict[str, object]] = []
        for team in summary.get("boxscore", {}).get("teams", []):
            row: Dict[str, object] = {"Équipe": team["team"]["displayName"]}
            for stat in team.get("statistics", []):
                row[stat["label"]] = stat.get("displayValue")
            records.append(row)
        df = pd.DataFrame(records)
        numeric_columns = [col for col in df.columns if col != "Équipe"]
        for column in numeric_columns:
            df[column] = df[column].apply(parse_numeric)
        percentage_columns = [col for col in df.columns if "%(" in col.lower() or "%" in col]
        for column in percentage_columns:
            df[column] = df[column].apply(lambda x: x * 100 if x is not None and x <= 1 else x)
        return df

    def _build_player_stats(self, summary: Dict) -> pd.DataFrame:
        rows: List[Dict[str, object]] = []
        for team in summary.get("rosters", []):
            team_name = team["team"]["displayName"]
            for player in team.get("roster", []):
                row: Dict[str, object] = {
                    "Équipe": team_name,
                    "Joueur": player["athlete"]["displayName"],
                    "N°": player.get("jersey"),
                    "Titulaire": bool(player.get("starter")),
                    "Poste": (player.get("position") or {}).get("abbreviation"),
                }
                for stat in player.get("stats", []):
                    row[stat["displayName"]] = stat.get("displayValue")
                rows.append(row)
        df = pd.DataFrame(rows)
        stat_cols = [col for col in df.columns if col not in {"Équipe", "Joueur", "N°", "Titulaire", "Poste"}]
        for column in stat_cols:
            df[column] = df[column].apply(parse_numeric)
        return df

    def _build_key_events(self, summary: Dict) -> pd.DataFrame:
        events_data: List[Dict[str, object]] = []
        for event in summary.get("keyEvents", []):
            events_data.append(
                {
                    "Minute": event.get("clock", {}).get("displayValue"),
                    "Période": event.get("period", {}).get("displayValue"),
                    "Type": (event.get("type") or {}).get("text"),
                    "Description": event.get("text"),
                }
            )
        df = pd.DataFrame(events_data)
        return df
