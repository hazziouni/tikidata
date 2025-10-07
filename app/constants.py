"""Application constants for supported leagues and seasons."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class LeagueConfig:
    """Configuration describing how to access an ESPN soccer competition."""

    name: str
    espn_slug: str
    aliases: tuple[str, ...]
    seasons: range

    @property
    def canonical(self) -> str:
        return self.aliases[0] if self.aliases else self.name


SUPPORTED_LEAGUES: Dict[str, LeagueConfig] = {
    "Premier League": LeagueConfig(
        name="Premier League",
        espn_slug="eng.1",
        aliases=("premier league", "epl", "premiership"),
        seasons=range(2019, 2026),
    ),
    "Ligue 1": LeagueConfig(
        name="Ligue 1",
        espn_slug="fra.1",
        aliases=("ligue 1", "ligue1", "france"),
        seasons=range(2019, 2026),
    ),
    "La Liga": LeagueConfig(
        name="La Liga",
        espn_slug="esp.1",
        aliases=("la liga", "laliga", "liga"),
        seasons=range(2019, 2026),
    ),
    "Serie A": LeagueConfig(
        name="Serie A",
        espn_slug="ita.1",
        aliases=("serie a", "italy", "seriea"),
        seasons=range(2019, 2026),
    ),
    "Bundesliga": LeagueConfig(
        name="Bundesliga",
        espn_slug="ger.1",
        aliases=("bundesliga", "germany"),
        seasons=range(2019, 2026),
    ),
}


def iter_all_aliases() -> Iterable[tuple[str, LeagueConfig]]:
    """Yield every supported league alias and its configuration."""

    for league in SUPPORTED_LEAGUES.values():
        for alias in (league.name.lower(), *league.aliases):
            yield alias, league


def list_season_labels(config: LeagueConfig) -> List[str]:
    """Return a display friendly list of available seasons for a league."""

    seasons = []
    for year in config.seasons:
        seasons.append(f"{year}-{year + 1}")
    return seasons
