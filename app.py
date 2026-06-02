from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import feedparser
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="Informe Diario de Mercado",
    page_icon="📈",
    layout="wide",
)

# -----------------------------
# Universo de mercado
# -----------------------------
INDEX_TICKERS: Dict[str, str] = {
    "S&P 500": "^GSPC",
    "Nasdaq 100": "^NDX",
    "Dow Jones": "^DJI",
    "EuroStoxx 50": "^STOXX50E",
    "DAX": "^GDAXI",
    "CAC 40": "^FCHI",
    "IBEX 35": "^IBEX",
    "Nikkei 225": "^N225",
    "Oro": "GC=F",
    "Petróleo Brent": "BZ=F",
    "EUR/USD": "EURUSD=X",
    "Bitcoin": "BTC-USD",
}

WATCHLIST: Dict[str, str] = {
    "Nvidia": "NVDA",
    "AMD": "AMD",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Alphabet": "GOOGL",
    "Amazon": "AMZN",
    "Meta": "META",
    "Tesla": "TSLA",
    "Broadcom": "AVGO",
    "Eli Lilly": "LLY",
    "Novo Nordisk": "NVO",
    "JPMorgan": "JPM",
    "Visa": "V",
    "ASML": "ASML.AS",
    "SAP": "SAP.DE",
    "Siemens": "SIE.DE",
    "Allianz": "ALV.DE",
    "LVMH": "MC.PA",
    "Airbus": "AIR.PA",
    "Santander": "SAN.MC",
    "BBVA": "BBVA.MC",
    "Inditex": "ITX.MC",
    "Iberdrola": "IBE.MC",
    "Aena": "AENA.MC",
    "Mercedes-Benz Group": "MBG.DE",
    "BMW": "BMW.DE",
    "Stellantis": "STLAM.MI",
    "Intuit": "INTU",
    "Domino's Pizza": "DPZ",
    "Nike": "NKE",
}

CORE_ETFS = [
    {
        "nombre": "Vanguard FTSE All-World UCITS ETF Acc",
        "isin": "IE00BK5BQT80",
        "ticker": "VWCE.DE",
        "rol": "Núcleo global",
        "justificacion": "Exposición mundial diversificada, adecuada como base de cartera para aportaciones periódicas.",
    },
    {
        "nombre": "iShares Core MSCI World UCITS ETF Acc",
        "isin": "IE00B4L5Y983",
        "ticker": "EUNL.DE",
        "rol": "Renta variable desarrollada",
        "justificacion": "Alternativa sólida para concentrar la cartera en mercados desarrollados con bajo coste.",
    },
    {
        "nombre": "Xtrackers II EUR Overnight Rate Swap UCITS ETF 1C",
        "isin": "LU0290358497",
        "ticker": "XEON.DE",
        "rol": "Liquidez remunerada defensiva",
        "justificacion": "Útil para aparcar liquidez si el mercado está caro o volátil, aunque depende del nivel de tipos del BCE.",
    },
]

RSS_FEEDS = {
    "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
    "CNBC Markets": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "MarketWatch": "https://feeds.content.dowjones.io/public/rss/mw_marketpulse",
    "Investing.com Economy": "https://www.investing.com/rss/news_95.rss",
}

# -----------------------------
# Carga y cálculo de datos
# -----------------------------
@st.cache_data(ttl=900, show_spinner=False)
def download_prices(tickers: Tuple[str, ...], period: str = "7d") -> pd.DataFrame:
    data = yf.download(
        list(tickers),
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False,
        group_by="ticker",
        threads=True,
    )
    return data


def last_change_from_download(data: pd.DataFrame, ticker: str) -> float | None:
    try:
        if isinstance(data.columns, pd.MultiIndex):
            close = data[ticker]["Close"].dropna()
        else:
            close = data["Close"].dropna()
        if len(close) < 2:
            return None
        return float((close.iloc[-1] / close.iloc[-2] - 1) * 100)
    except Exception:
        return None


@st.cache_data(ttl=900, show_spinner=False)
def get_market_snapshot() -> pd.DataFrame:
    data = download_prices(tuple(INDEX_TICKERS.values()), period="7d")
    rows = []
    reverse = {v: k for k, v in INDEX_TICKERS.items()}
    for ticker in INDEX_TICKERS.values():
        pct = last_change_from_download(data, ticker)
        if pct is not None:
            rows.append({"Activo": reverse[ticker], "Ticker": ticker, "Variación %": round(pct, 2)})
    return pd.DataFrame(rows)


@st.cache_data(ttl=900, show_spinner=False)
def get_watchlist_movers() -> pd.DataFrame:
    data = download_prices(tuple(WATCHLIST.values()), period="7d")
    reverse = {v: k for k, v in WATCHLIST.items()}
    rows = []
    for ticker in WATCHLIST.values():
        pct = last_change_from_download(data, ticker)
        if pct is not None:
            rows.append({"Acción": reverse[ticker], "Ticker": ticker, "%": round(pct, 2)})
    return pd.DataFrame(rows).sort_values("%", ascending=False)


@st.cache_data(ttl=1800, show_spinner=False)
def get_news(max_items: int = 8) -> List[dict]:
    items: List[dict] = []
    for source, url in RSS_FEEDS.items():
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:4]:
                items.append(
                    {
                        "fuente": source,
                        "titulo": entry.get("title", "Sin título"),
                        "link": entry.get("link", ""),
                        "fecha": entry.get("published", entry.get("updated", "")),
                    }
                )
        except Exception:
            continue
    return items[:max_items]


def build_summary(snapshot: pd.DataFrame) -> str:
    if snapshot.empty:
        return "No se han podido cargar datos suficientes. Revisa la conexión o inténtalo de nuevo más tarde."

    equity_names = ["S&P 500", "Nasdaq 100", "EuroStoxx 50", "DAX", "IBEX 35"]
    equities = snapshot[snapshot["Activo"].isin(equity_names)]
    avg_equity = equities["Variación %"].mean() if not equities.empty else np.nan
    best = snapshot.sort_values("Variación %", ascending=False).iloc[0]
    worst = snapshot.sort_values("Variación %", ascending=True).iloc[0]

    tone = "positiva" if avg_equity > 0.25 else "negativa" if avg_equity < -0.25 else "mixta/lateral"
    return (
        f"La jornada anterior tuvo una lectura **{tone}** para la renta variable global. "
        f"La variación media de los principales índices seguidos fue de **{avg_equity:.2f}%**. "
        f"El mejor comportamiento relativo vino de **{best['Activo']}** con **{best['Variación %']:.2f}%**, "
        f"mientras que el activo más débil fue **{worst['Activo']}** con **{worst['Variación %']:.2f}%**.\n\n"
        "Para la sesión actual, la prioridad es distinguir si el movimiento viene apoyado por amplitud de mercado "
        "o si está concentrado en pocos valores. Si la subida depende solo de tecnología/mega caps, conviene no perseguir precios."
    )


def build_recommendation(snapshot: pd.DataFrame, movers: pd.DataFrame) -> str:
    if snapshot.empty:
        return "Sin datos suficientes para emitir una recomendación táctica."
    sp = snapshot.loc[snapshot["Activo"] == "S&P 500", "Variación %"]
    ndx = snapshot.loc[snapshot["Activo"] == "Nasdaq 100", "Variación %"]
    eur = snapshot.loc[snapshot["Activo"] == "EuroStoxx 50", "Variación %"]
    sp_v = float(sp.iloc[0]) if not sp.empty else 0.0
    ndx_v = float(ndx.iloc[0]) if not ndx.empty else 0.0
    eur_v = float(eur.iloc[0]) if not eur.empty else 0.0

    if sp_v > 0.5 and ndx_v > 0.5:
        stance = "constructiva pero selectiva"
        detail = "El impulso de EE. UU. favorece mantener aportaciones periódicas al núcleo global, evitando compras agresivas en valores que ya hayan corrido mucho."
    elif sp_v < -0.5 or ndx_v < -0.8:
        stance = "defensiva"
        detail = "La presión en índices estadounidenses recomienda priorizar liquidez, aportaciones escalonadas y evitar aumentar exposición en valores de beta alta."
    elif eur_v > sp_v:
        stance = "moderadamente favorable a Europa"
        detail = "Europa muestra mejor tono relativo. Tiene sentido vigilar calidad europea e industriales, sin concentrar demasiado en automoción."
    else:
        stance = "neutral"
        detail = "El mercado no muestra una señal direccional clara. La mejor decisión suele ser mantener el plan de aportaciones y reservar liquidez para caídas."

    return (
        f"**Sesgo para la jornada actual: {stance}.** {detail}\n\n"
        "Para una cartera como la de David, que ya tiene exposición a Mercedes-Benz, BMW, Stellantis, Aena, Intuit y Domino's, "
        "no conviene añadir más concentración sectorial salvo oportunidades muy claras. La prioridad debe seguir siendo reforzar el núcleo global "
        "y usar posiciones tácticas pequeñas solo cuando el binomio riesgo/recompensa sea evidente."
    )


def style_pct(v: float) -> str:
    return f"{v:+.2f}%"

# -----------------------------
# Interfaz
# -----------------------------
st.title("📈 Informe Diario de Mercado")
st.caption("Dashboard para revisar mercado, noticias, valores fuertes/débiles y ETFs clave para una cartera en Trade Republic.")

with st.sidebar:
    st.header("Configuración")
    st.write("Actualización automática de datos cada 15 minutos mientras la app esté abierta.")
    selected_market = st.multiselect(
        "Activos de mercado visibles",
        list(INDEX_TICKERS.keys()),
        default=["S&P 500", "Nasdaq 100", "EuroStoxx 50", "DAX", "IBEX 35", "EUR/USD", "Oro", "Bitcoin"],
    )
    top_n = st.slider("Número de acciones en tablas", 5, 15, 10)
    st.divider()
    st.write("Cartera base considerada:")
    st.write("VWCE como núcleo global + posiciones tácticas en Intuit, Domino's, Mercedes, BMW, Aena, Stellantis y Nike.")

snapshot = get_market_snapshot()
movers = get_watchlist_movers()
news = get_news()

# Métricas principales
visible_snapshot = snapshot[snapshot["Activo"].isin(selected_market)] if selected_market else snapshot
cols = st.columns(min(4, max(1, len(visible_snapshot))))
for i, (_, row) in enumerate(visible_snapshot.head(8).iterrows()):
    cols[i % len(cols)].metric(row["Activo"], style_pct(row["Variación %"]), row["Ticker"])

st.divider()

st.header("1. Resumen de la Jornada Anterior")
st.markdown(build_summary(snapshot))

st.header("2. Noticias Económicas Relevantes")
if news:
    for item in news[:5]:
        link = item["link"]
        title = item["titulo"]
        source = item["fuente"]
        if link:
            st.markdown(f"- **[{title}]({link})** — {source}. Impacto potencial: puede afectar al sentimiento de mercado, tipos, divisas o sectores sensibles al ciclo.")
        else:
            st.markdown(f"- **{title}** — {source}. Impacto potencial: puede afectar al sentimiento de mercado.")
else:
    st.warning("No se han podido cargar noticias RSS en este momento.")

left, right = st.columns(2)
with left:
    st.header("3. Top Acciones - Subidas")
    top_up = movers.head(top_n).copy()
    top_up["% de Subida"] = top_up["%"].map(lambda x: f"{x:+.2f}%")
    st.dataframe(top_up[["Acción", "Ticker", "% de Subida"]], use_container_width=True, hide_index=True)

with right:
    st.header("4. Top Acciones - Bajadas")
    top_down = movers.tail(top_n).sort_values("%", ascending=True).copy()
    top_down["% de Bajada"] = top_down["%"].map(lambda x: f"{x:+.2f}%")
    st.dataframe(top_down[["Acción", "Ticker", "% de Bajada"]], use_container_width=True, hide_index=True)

st.header("5. Análisis y Recomendaciones de Inversión")
st.markdown(build_recommendation(snapshot, movers))
st.info(
    "Esto no es asesoramiento financiero personalizado. Úsalo como filtro diario: confirma valoración, riesgo y tamaño de posición antes de comprar."
)

st.header("6. ETFs y Fondos de Inversión disponibles en Trade Republic")
for etf in CORE_ETFS:
    with st.expander(f"{etf['nombre']} — {etf['isin']} ({etf['rol']})", expanded=True):
        st.write(etf["justificacion"])
        st.write(f"Ticker orientativo: `{etf['ticker']}`. Comprueba siempre disponibilidad, divisa, spread y TER en Trade Republic antes de operar.")

st.divider()
st.caption(f"Última actualización de la app: {datetime.now().strftime('%d/%m/%Y %H:%M')}. Datos de mercado vía Yahoo Finance/yfinance y noticias vía RSS públicos.")
