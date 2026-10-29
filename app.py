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
API_KEY = st.secrets.get("API_FOOTBALL_KEY", os.getenv("API_FOOTBALL_KEY", "")).strip()

TOP_LEAGUES = {
    39: "Premier League",
    140: "La Liga",
    135: "Serie A",
    78: "Bundesliga",
    61: "Ligue 1",
    2: "UEFA Champions League",
    3: "UEFA Europa League",
}
