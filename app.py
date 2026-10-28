import os
from datetime import date, datetime
from collections import defaultdict

import pandas as pd
import requests
import streamlit as st

# Football Stats Analyzer - MVP
# Provider: API-Football (API-Sports), REST API v3
# Keep your API key secret: set API_FOOTBALL_KEY as an environment variable.

API_BASE = "https://v3.football.api-sports.io"
API_KEY = os.getenv("API_FOOTBALL_KEY", "").strip()

TOP_LEAGUES = {
    39: "Premier League",
    140: "La Liga",
    135: "Serie A",
    78: "Bundesliga",
    61: "Ligue 1",
    2: "UEFA Champions League",
    3: "UEFA Europa League",
}

STAT_MAP = {
    "Total Shots": "tiri",
    "Shots on Goal": "tiri_in_porta",
    "Corner Kicks": "corner",
    "Fouls": "falli",
    "Yellow Cards": "gialli",
    "Red Cards": "rossi",
    "Total Goals": "gol",
}

st.set_page_config(page_title="Football Stats Analyzer", page_icon="⚽", layout="wide")
st.title("⚽ Football Stats Analyzer")
st.caption("Prototipo MVP · statistiche calcistiche da API-Football")

if not API_KEY:
    st.warning(
        "Per caricare dati reali, imposta la variabile d'ambiente API_FOOTBALL_KEY "
        "con la tua chiave API-Football. Senza chiave puoi esplorare la struttura "
        "dell'app, ma i dati reali non vengono caricati."
    )

@st.cache_data(ttl=300, show_spinner=False)
def api_get(endpoint: str, params: tuple = ()):
    if not API_KEY:
        return []
    headers = {"x-apisports-key": API_KEY}
    response = requests.get(
        f"{API_BASE}/{endpoint}",
        headers=headers,
        params=dict(params),
        timeout=25,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(str(payload["errors"]))
    return payload.get("response", [])

def get_fixtures(day: date):
    return api_get("fixtures", (("date", day.isoformat()),))

def get_fixture_stats(fixture_id: int):
    return api_get("fixtures/statistics", (("fixture", fixture_id),))

def get_team_recent_fixtures(team_id: int, season: int, count: int = 5):
    return api_get(
        "fixtures",
        (("team", team_id), ("season", season), ("last", count), ("status", "FT")),
    )

def stats_to_dict(stats_response):
    output = {}
    for team_block in stats_response or []:
        team_name = (team_block.get("team") or {}).get("name", "Squadra")
        values = {}
        for item in team_block.get("statistics") or []:
            name = item.get("type")
            value = item.get("value")
            if isinstance(value, str) and value.endswith("%"):
                try:
                    value = float(value[:-1])
                except ValueError:
                    pass
            values[name] = value
        output[team_name] = values
    return output

def num(value):
    if value is None or value == "":
        return None
    if isinstance(value, str) and value.endswith("%"):
        value = value[:-1]
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def fixture_label(f):
    league = (f.get("league") or {}).get("name", "Campionato")
    teams = f.get("teams") or {}
    home = (teams.get("home") or {}).get("name", "?")
    away = (teams.get("away") or {}).get("name", "?")
    kickoff = (f.get("fixture") or {}).get("date", "")
    try:
        kickoff = datetime.fromisoformat(kickoff.replace("Z", "+00:00")).strftime("%H:%M")
    except Exception:
        kickoff = "--:--"
    return f"{kickoff} · {league} · {home} - {away}"

def recent_team_average(team_id: int, season: int, target_team_name: str, count: int = 5):
    """Average recent team stats. Each unique historical fixture costs one API request for stats."""
    matches = get_team_recent_fixtures(team_id, season, count)
    if not matches:
        return None, 0
    sums = defaultdict(float)
    seen = defaultdict(int)
    team_matches_used = 0
    for match in matches:
        fixture = match.get("fixture") or {}
        fixture_id = fixture.get("id")
        if not fixture_id:
            continue
        blocks = stats_to_dict(get_fixture_stats(int(fixture_id)))
        team_values = blocks.get(target_team_name)
        if team_values is None:
            # Use the fixture's home/away IDs to identify the correct stats block more safely.
            target_id = team_id
            home = (match.get("teams") or {}).get("home") or {}
            away = (match.get("teams") or {}).get("away") or {}
            target_name = home.get("name") if home.get("id") == target_id else away.get("name")
            team_values = blocks.get(target_name, {})
        for api_name, short_name in STAT_MAP.items():
            value = num(team_values.get(api_name))
            if value is not None:
                sums[short_name] += value
                seen[short_name] += 1
        # Goals are more reliably available from fixture score fields.
        goals = (match.get("goals") or {})
        home = (match.get("teams") or {}).get("home") or {}
        away = (match.get("teams") or {}).get("away") or {}
        if home.get("id") == team_id:
            goal_value = num(goals.get("home"))
        else:
            goal_value = num(goals.get("away"))
        if goal_value is not None:
            sums["gol"] += goal_value
            seen["gol"] += 1
        team_matches_used += 1
    averages = {key: round(sums[key] / seen[key], 2) for key in sums if seen[key]}
    return averages, team_matches_used

def show_value(value):
    return "n/d" if value is None else (str(int(value)) if float(value).is_integer() else str(value))

if not API_KEY:
    st.subheader("Cosa farà il prototipo")
    cols = st.columns(5)
    for col, label, value in zip(
        cols,
        ["Falli", "Cartellini", "Tiri in porta", "Corner", "Gol"],
        ["commessi", "gialli/rossi", "totali", "a favore", "fatti/subiti"],
    ):
        col.metric(label, "—", value)
    st.info("Dopo aver configurato la chiave API, scegli una data e carica le partite.")
    st.stop()

with st.sidebar:
    st.header("Filtri")
    selected_date = st.date_input("Data partite", value=date.today())
    league_filter = st.multiselect(
        "Campionati principali",
        options=list(TOP_LEAGUES.keys()),
        default=list(TOP_LEAGUES.keys()),
        format_func=lambda league_id: TOP_LEAGUES[league_id],
    )
    recent_count = st.select_slider("Partite recenti per squadra", options=[3, 5, 8, 10], value=5)
    st.caption("Nota: il numero di richieste API cresce quando analizzi molte partite.")

try:
    with st.spinner("Caricamento calendario..."):
        all_fixtures = get_fixtures(selected_date)
except Exception as exc:
    st.error(f"Errore nel caricamento del calendario: {exc}")
    st.stop()

fixtures = [
    f for f in all_fixtures
    if ((f.get("league") or {}).get("id") in league_filter)
]
st.subheader(f"Partite del {selected_date.strftime('%d/%m/%Y')}")
st.caption(f"{len(fixtures)} partite trovate nei campionati selezionati.")

if not fixtures:
    st.info("Nessuna partita trovata per la data e i campionati scelti.")
    st.stop()

labels = [fixture_label(f) for f in fixtures]
chosen_label = st.selectbox("Scegli una partita da analizzare", labels)
chosen = fixtures[labels.index(chosen_label)]
fixture = chosen.get("fixture") or {}
teams = chosen.get("teams") or {}
home = teams.get("home") or {}
away = teams.get("away") or {}
league = chosen.get("league") or {}
season = int(league.get("season") or selected_date.year)

a, b, c = st.columns(3)
a.metric("Campionato", league.get("name", "n/d"))
b.metric("Casa", home.get("name", "n/d"))
c.metric("Trasferta", away.get("name", "n/d"))

status = ((fixture.get("status") or {}).get("short")) or ""
if status in {"FT", "AET", "PEN", "1H", "2H", "HT", "ET", "BT", "LIVE"}:
    try:
        with st.spinner("Caricamento statistiche della partita..."):
            match_stats = stats_to_dict(get_fixture_stats(int(fixture["id"])))
        st.markdown("### Statistiche della partita")
        home_stats = match_stats.get(home.get("name"), {})
        away_stats = match_stats.get(away.get("name"), {})
        rows = []
        for api_name, display_name in [
            ("Fouls", "Falli"),
            ("Yellow Cards", "Cartellini gialli"),
            ("Red Cards", "Cartellini rossi"),
            ("Total Shots", "Tiri totali"),
            ("Shots on Goal", "Tiri in porta"),
            ("Corner Kicks", "Corner"),
        ]:
            rows.append({
                "Statistica": display_name,
                home.get("name", "Casa"): show_value(num(home_stats.get(api_name))),
                away.get("name", "Trasferta"): show_value(num(away_stats.get(api_name))),
            })
        score = chosen.get("goals") or {}
        rows.append({
            "Statistica": "Gol",
            home.get("name", "Casa"): show_value(num(score.get("home"))),
            away.get("name", "Trasferta"): show_value(num(score.get("away"))),
        })
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    except Exception as exc:
        st.warning(f"Le statistiche di questa partita non sono disponibili o si è verificato un errore: {exc}")
else:
    st.info("La partita non è ancora iniziata. Puoi calcolare le medie recenti delle due squadre qui sotto.")

st.markdown("### Medie delle ultime partite")
if st.button("Calcola medie recenti per questa partita", type="primary"):
    try:
        with st.spinner(f"Recupero delle ultime {recent_count} partite per squadra..."):
            home_avg, home_n = recent_team_average(
                int(home["id"]), season, home.get("name", ""), recent_count
            )
            away_avg, away_n = recent_team_average(
                int(away["id"]), season, away.get("name", ""), recent_count
            )
        if not home_avg and not away_avg:
            st.warning("Non ci sono statistiche storiche disponibili per queste squadre/stagione.")
        else:
            metrics = [
                ("Falli", "falli"),
                ("Gialli", "gialli"),
                ("Rossi", "rossi"),
                ("Tiri", "tiri"),
                ("Tiri in porta", "tiri_in_porta"),
                ("Corner", "corner"),
                ("Gol fatti", "gol"),
            ]
            rows = []
            for label, key in metrics:
                rows.append({
                    "Media per partita": label,
                    home.get("name", "Casa"): show_value((home_avg or {}).get(key)),
                    away.get("name", "Trasferta"): show_value((away_avg or {}).get(key)),
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            st.caption(
                f"Campione effettivo: {home_n} partite per {home.get('name')} e "
                f"{away_n} per {away.get('name')}. Valori mancanti non vengono stimati."
            )
            st.warning(
                "Queste sono medie descrittive, non probabilità garantite. "
                "Il prototipo non formula ancora raccomandazioni automatiche."
            )
    except Exception as exc:
        st.error(f"Non è stato possibile calcolare le medie: {exc}")

with st.expander("Come leggere i dati"):
    st.write(
        "- Le statistiche pre-partita sono calcolate sulle ultime partite concluse disponibili.\n"
        "- La copertura varia per campionato: alcuni provider non registrano ogni statistica in tutte le leghe.\n"
        "- Le chiamate sono memorizzate temporaneamente per ridurre il consumo della quota API.\n"
        "- Prima di usare il sistema per analisi serie, verifica le statistiche con i dati ufficiali del provider."
    )
