# app_streamlit.py

import streamlit as st
from dateutil.parser import isoparse
from datetime import datetime, timezone

# ── 1) CONFIGURACIÓN DE PÁGINA ──────────────────────────────────────────────
st.set_page_config(
    page_title="⚽ Live Value Bets",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 2) SECRETOS & SIDEBAR ────────────────────────────────────────────────────
api_key = st.secrets["API_FOOTBALL_KEY"]
season = st.sidebar.number_input("Temporada", value=2024, min_value=2000, max_value=2100, step=1)

TOP5 = {39:"Premier League",78:"Bundesliga",140:"LaLiga",135:"Serie A",61:"Ligue 1"}
league_id = st.sidebar.selectbox("Liga", options=list(TOP5.keys()), format_func=lambda x: TOP5[x])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Umbrales")
p_threshold = st.sidebar.slider("Probabilidad mínima (%)", 0, 100, 60, 5) / 100.0
value_threshold = st.sidebar.slider("Umbral Value Bet (%)", 0, 100, 70, 5) / 100.0

# ── 3) FETCH DE DATOS ─────────────────────────────────────────────────────────
from data_ingest import fetch_live_fixtures, fetch_upcoming_fixtures, fetch_odds_for_fixture
from app import calcular_probabilidades_desde_cuotas
from enrichment.motivation import motivation_factor

with st.spinner("🔄 Cargando partidos…"):
    live = fetch_live_fixtures(api_key)
    matches = [f for f in live if f["league"]["id"] == league_id]
    if not matches:
        futuros = fetch_upcoming_fixtures(league_id, season, api_key)
        ahora = datetime.now(timezone.utc)
        matches = [f for f in futuros if isoparse(f["fixture"]["date"]) > ahora][:10]

# ── 4) SELECTOR DE PARTIDO ────────────────────────────────────────────────────
labels = [
    f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}  |  "
    f"{isoparse(f['fixture']['date']).astimezone().strftime('%d %b %H:%M')}"
    for f in matches
]
sel_idx = st.sidebar.selectbox("Partido", range(len(labels)), format_func=lambda i: labels[i])
sel = matches[sel_idx]
home = sel["teams"]["home"]["name"]
away = sel["teams"]["away"]["name"]
kickoff = isoparse(sel["fixture"]["date"]).astimezone().strftime("%A %d %b %Y %H:%M")

# ── 5) CABECERA ───────────────────────────────────────────────────────────────
st.markdown(f"## ⚽ {home} vs {away}")
col1, col2 = st.columns([3,1])
with col1:
    st.markdown(f"**Inicio:** {kickoff}")
    mot = motivation_factor(sel["league"]["round"], total_rounds=38)
    st.markdown(f"**Motivación (1–3):** {mot}")
with col2:
    st.metric("Liga", TOP5[league_id])
    st.metric("Temporada", season)

# ── 6) FETCH CUOTAS ───────────────────────────────────────────────────────────
odds = fetch_odds_for_fixture(sel["fixture"]["id"], api_key)

# ── 7) PREPARAR DATOS DE ODDS ─────────────────────────────────────────────────
bookie_odds = {}
for offer in odds:
    bm = offer.get("bookmaker", {}).get("name", "Desconocido")
    for bet in offer.get("bets", []):
        if bet["name"] in ("Match Winner","1X2"):
            m = {v["value"]:v["odd"] for v in bet["values"]}
            if home in m and "Draw" in m and away in m:
                bookie_odds[bm] = {"Local":m[home],"Empate":m["Draw"],"Visitante":m[away]}

if not bookie_odds:
    st.error("🚨 No hay datos de cuotas disponibles para este partido.")
    st.stop()

first = next(iter(bookie_odds.values()))
p_l, p_e, p_v = calcular_probabilidades_desde_cuotas(
    first["Local"], first["Empate"], first["Visitante"]
)

# ── 8) SELECCIÓN DE CASAS PRINCIPALES ─────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown("### 🏟 Casas para mostrar")
all_bookies = list(bookie_odds.keys())
default_bookies = all_bookies[:5]
sel_bookies = st.sidebar.multiselect("Casas", options=all_bookies, default=default_bookies)

# ── 9) APUESTAS ≥ P_THRESHOLD ─────────────────────────────────────────────────
st.subheader(f"🔍 Apuestas con probabilidad ≥ {int(p_threshold*100)}%")
rows = []
for bm in sel_bookies:
    o = bookie_odds[bm]
    for esc, odd in o.items():
        prob = {"Local":p_l,"Empate":p_e,"Visitante":p_v}[esc]
        if prob >= p_threshold:
            rows.append({"Bookmaker": bm, "Escenario": esc, "Cuota": f"{odd:.2f}", "Prob (%)": f"{prob*100:.1f}"})
if rows:
    st.table(rows)
else:
    st.info("Ninguna casa ofrece escenarios con esa probabilidad.")

# ── 10) VALUE BETS (P≥VALUE_THRESHOLD y Δ>0) ─────────────────────────────────
st.subheader(f"💥 Value Bets (P≥{int(value_threshold*100)}% & mercado recorta)")
value_rows = []
for esc in ["Local","Empate","Visitante"]:
    odds_list = [o[esc] for o in bookie_odds.values()]
    current_odd = min(odds_list)
    delta = max(odds_list) - current_odd
    prob = {"Local":p_l,"Empate":p_e,"Visitante":p_v}[esc]
    if prob >= value_threshold and delta > 0:
        value_rows.append({
            "Escenario": esc,
            "Prob (%)": f"{prob*100:.1f}",
            "Cuota mínima": f"{current_odd:.2f}",
            "Rango": f"{min(odds_list):.2f}–{max(odds_list):.2f}",
            "Δ cuota": f"{delta:.2f}"
        })
if value_rows:
    st.table(value_rows)
else:
    st.info("No hay value bets detectadas.")

# ── 11) BTTS (placeholder) ────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🔒 BTTS (próximo)")
st.write("Cálculo de probabilidad BTTS pendiente de implementar.")
