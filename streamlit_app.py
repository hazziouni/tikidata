"""Streamlit dashboard that showcases scraped football match analytics."""

from __future__ import annotations

from datetime import timezone
from typing import List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.constants import SUPPORTED_LEAGUES, list_season_labels
from app.match_service import MatchLookupError, MatchService, TeamLookupError


st.set_page_config(
    page_title="Analyse de match football",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)


def display_team_kpis(team_df: pd.DataFrame, home_name: str, away_name: str) -> None:
    if team_df.empty or "Équipe" not in team_df.columns:
        st.warning("Aucune statistique d'équipe disponible.")
        return
    kpi_candidates = [
        ("SHOTS", "Tirs"),
        ("ON GOAL", "Tirs cadrés"),
        ("Possession", "Possession %"),
        ("Pass Completion %", "Précision des passes %"),
        ("Tackles", "Tacles"),
    ]
    data = {}
    for label, title in kpi_candidates:
        if label in team_df.columns:
            data[title] = team_df[["Équipe", label]].rename(columns={label: title})
    if not data:
        st.warning("Les statistiques clés ne sont pas disponibles.")
        return

    tabs = st.tabs(list(data.keys()))
    for tab, (stat_name, df) in zip(tabs, data.items()):
        with tab:
            fig = go.Figure()
            home_series = df[df["Équipe"] == home_name][stat_name]
            away_series = df[df["Équipe"] == away_name][stat_name]
            home_value = home_series.iloc[0] if not home_series.empty else 0
            away_value = away_series.iloc[0] if not away_series.empty else 0
            fig.add_bar(name=home_name, x=[home_name], y=[home_value])
            fig.add_bar(name=away_name, x=[away_name], y=[away_value])
            fig.update_layout(
                barmode="group",
                showlegend=False,
                yaxis_title=stat_name,
                template="plotly_white",
                height=340,
            )
            st.plotly_chart(fig, use_container_width=True)


def show_player_filters(players: pd.DataFrame) -> None:
    if players.empty:
        st.warning("Les statistiques individuelles ne sont pas disponibles.")
        return
    teams = sorted(players["Équipe"].unique())
    selected_team = st.selectbox("Sélectionnez une équipe", teams)
    filtered = players[players["Équipe"] == selected_team]
    player_names: List[str] = filtered["Joueur"].tolist()
    selected_players = st.multiselect("Choisissez un ou plusieurs joueurs", player_names, default=player_names[:3])
    if not selected_players:
        st.info("Sélectionnez au moins un joueur pour afficher ses données.")
        return
    table = filtered[filtered["Joueur"].isin(selected_players)]
    st.dataframe(table.set_index("Joueur"), use_container_width=True)


service = MatchService()

st.title("Tableau de bord d'analyse de match")
st.caption("Les données sont récupérées en direct depuis les endpoints publics d'ESPN.")

with st.sidebar:
    st.header("Paramètres")
    league_name = st.selectbox("Championnat", list(SUPPORTED_LEAGUES.keys()))
    league_config = SUPPORTED_LEAGUES[league_name]
    seasons = list_season_labels(league_config)
    default_season = seasons[-2] if len(seasons) >= 2 else seasons[-1]
    season = st.selectbox("Saison", seasons, index=seasons.index(default_season))
    home_team = st.text_input("Équipe à domicile", "Paris Saint-Germain")
    away_team = st.text_input("Équipe à l'extérieur", "Olympique de Marseille")
    run = st.button("Analyser le match")

if run:
    try:
        with st.spinner("Chargement des données du match..."):
            match = service.load_match(league_name, season, home_team, away_team)
    except ValueError as exc:
        st.error(str(exc))
    except TeamLookupError as exc:
        st.error(str(exc))
    except MatchLookupError as exc:
        st.error(str(exc))
    else:
        metadata = match.metadata
        home = metadata.scoreline.get("home")
        away = metadata.scoreline.get("away")
        if not home or not away:
            st.warning("Impossible d'afficher le score du match.")
        else:
            st.subheader(f"{home.team} vs {away.team}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Score", f"{home.score} - {away.score}")
            with col2:
                kickoff = metadata.start_time.astimezone(timezone.utc)
                st.metric("Date", kickoff.strftime("%d %b %Y %H:%M UTC"))
            with col3:
                location = metadata.venue or "-"
                st.metric("Stade", location)

            st.markdown("### Statistiques d'équipe clés")
            display_team_kpis(match.team_stats, home.team, away.team)

            st.markdown("### Statistiques complètes des équipes")
            st.dataframe(match.team_stats.set_index("Équipe"), use_container_width=True)

            st.markdown("### Analyse des joueurs")
            show_player_filters(match.player_stats)

            if not match.key_events.empty:
                st.markdown("### Temps forts du match")
                st.dataframe(match.key_events, use_container_width=True)
            else:
                st.info("Aucun temps fort disponible pour ce match.")
else:
    st.info("Configurez vos paramètres dans la barre latérale puis cliquez sur *Analyser le match*.")
