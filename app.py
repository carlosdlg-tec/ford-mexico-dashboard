"""
Ford Mexico, 2015-2025: where to invest next.
Strategy dashboard built on INEGI RAIAVL light-vehicle retail sales.

Buckets:  01 Ford today  |  02 Industry  |  03 Customer preferences  |  Recommendations

Run locally (from this folder, so the Ford theme in .streamlit/config.toml is used):
    streamlit run app.py
"""
import base64
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────────────────────────────────────
# Page + design tokens
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ford Mexico · Investment Strategy",
    page_icon=":material/directions_car:",
    layout="wide",
    initial_sidebar_state="expanded",
)

HERE = Path(__file__).resolve().parent
FILE = "INEGI_Auto_Ventas_Maestro_2015_2025.xlsx"
DATA = next((p / FILE for p in (HERE, HERE.parent, HERE / "data") if (p / FILE).exists()), HERE.parent / FILE)
LOGO = HERE / "ford_logo.svg"  # Ford oval, Wikimedia Commons; trademark of Ford Motor Company
LOGO_SRC = f"data:image/svg+xml;base64,{base64.b64encode(LOGO.read_bytes()).decode()}" if LOGO.exists() else ""

# Ford palette
NAVY = "#00095B"        # Ford Blue: headings, hero
FORD = "#1F4FB8"        # Ford as a data series (protagonist)
FORD_LT = "#9DBBF2"     # earlier-year / secondary Ford shade
RIVAL = "#7A8499"       # comparison company
CONTEXT = "#C9CFDA"     # everyone else
POS, NEG = "#1F4FB8", "#C2413A"  # diverging poles (growth / decline)
INK, INK2, MUTED = "#0B1530", "#3E4A66", "#7A849B"
GRID, AXIS = "#E7EAF1", "#C9CFDA"
FONT = '"Open Sans", Arial, sans-serif'
BAND_COVID = "rgba(0,9,91,0.09)"
BAND_CHIP = "rgba(0,9,91,0.045)"

# Segment identity colors (validated: CVD-safe adjacent order, see README)
SEG_ORDER = ["SUVs", "Pickups", "Minivans", "Luxury", "Subcompact", "Sports", "Compact"]
SEG_COL = {
    "SUVs": "#1F4FB8", "Pickups": "#12A0B0", "Minivans": "#D98E04", "Luxury": "#C2508F",
    "Subcompact": "#6FA0F0", "Sports": "#C2413A", "Compact": "#8A63C9",
}
SEG_EN = {
    "SUV's": "SUVs", "Pick Ups": "Pickups", "Minivans": "Minivans", "De Lujo": "Luxury",
    "Subcompactos": "Subcompact", "Deportivos": "Sports", "Compactos": "Compact",
}
# Electrified technologies (ordinal green ramp: HEV -> PHEV -> BEV)
TECH_COL = {"Hybrid (HEV)": "#6CC49C", "Plug-in (PHEV)": "#2E9A6F", "Electric (BEV)": "#11603F"}

BRAND_NAME = {
    "Ford Motor": "Ford", "General Motors": "GM (Chevrolet, GMC, Buick, Cadillac)",
    "Chrysler": "Stellantis (Jeep, RAM, Dodge, Chrysler)", "Mercedes Benz": "Mercedes-Benz",
    "KIA": "Kia", "JETOUR": "Jetour", "MOTORNATION": "Motornation",
}
COUNTRY_EN = {
    "Estados Unidos": "United States", "Canadá": "Canada", "Japón": "Japan", "Italia": "Italy",
    "Bélgica": "Belgium", "Alemania": "Germany", "España": "Spain", "Eslovaquia": "Slovakia",
    "Hungría": "Hungary", "Reino Unido": "United Kingdom", "Tailandia": "Thailand", "México": "Mexico",
    "Corea del Sur": "South Korea", "Brasil": "Brazil", "India": "India", "Argentina": "Argentina",
    "República Checa": "Czechia", "Austria": "Austria", "Francia": "France", "Colombia": "Colombia",
    "Países Bajos": "Netherlands", "Indonesia": "Indonesia", "Polonia": "Poland", "Suecia": "Sweden",
    "Serbia": "Serbia", "China": "China", "Turquía": "Turkey", "No Especificado": "Not specified",
    "Finlandia": "Finland",
}
TIPO_EN = {"Automóviles": "Cars", "Camiones ligeros": "Light trucks"}

PRESETS = {
    "Full decade": (2015, 2025),
    "Pre-COVID": (2015, 2019),
    "COVID + chips": (2019, 2022),
    "Recovery": (2020, 2025),
    "Post-shortage": (2022, 2025),
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;500;600;700;800&display=swap');
.block-container {{padding-top: 3.2rem; padding-bottom: 3rem; max-width: 1320px;}}
html, body, .stApp, .stApp *:not([data-testid="stIconMaterial"]):not([translate="no"]) {{font-family: {FONT} !important;}}
/* Hero colours are taken from the Ford oval: deep navy #08142E -> #17326E -> #0D69A9, highlight #4CA9E3, chrome rim #D3D2D2 */
.hero {{border-radius: 18px; padding: 30px 34px 26px; color: #fff; margin-bottom: 6px;
  border: 1px solid rgba(211,210,210,.28); box-shadow: inset 0 1px 0 rgba(255,255,255,.12);
  background: radial-gradient(520px 260px at 88% 18%, rgba(76,169,227,.38), transparent 70%),
              linear-gradient(120deg, #08142E 0%, #17326E 52%, #0D69A9 100%);}}
.hero-top {{display: flex; justify-content: space-between; align-items: center; gap: 24px;}}
.hero-logo {{width: clamp(110px, 15vw, 190px); height: auto; flex-shrink: 0;
  filter: drop-shadow(0 6px 14px rgba(5,17,37,.55));}}
.hero .eyebrow {{letter-spacing: .2em; text-transform: uppercase; font-size: 12px; color: #7CC3EE; font-weight: 600;}}
.hero h1 {{font-size: clamp(28px, 3.6vw, 44px); line-height: 1.08; margin: 8px 0 6px; color: #fff; font-weight: 750; padding: 0;}}
.hero .sub {{font-size: 15.5px; color: #D3E3F3; margin: 0;}}
.hero-stats {{display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin-top: 22px;}}
.hero-stat {{background: rgba(8,20,46,.32); border: 1px solid rgba(211,210,210,.22); border-top: 2px solid #4CA9E3;
  border-radius: 12px; padding: 12px 16px;}}
.hero-stat .lbl {{font-size: 11.5px; color: #B9D8F0; text-transform: uppercase; letter-spacing: .08em;}}
.hero-stat .val {{font-size: 26px; font-weight: 700; margin-top: 2px; color: #fff;}}
.hero-stat .val small {{font-size: 14px; color: #B9D8F0; font-weight: 500;}}
@media (max-width: 640px) {{.hero-top {{flex-direction: column-reverse; align-items: flex-start;}} .hero-logo {{width: 110px;}}}}
.sec {{display: flex; align-items: center; gap: 12px; margin: 26px 0 4px;}}
.sec .num {{background: {NAVY}; color: #fff; font-weight: 700; font-size: 13px; border-radius: 8px; padding: 4px 9px;}}
.sec h3 {{margin: 0; padding: 0; font-size: 22px; color: {INK}; font-weight: 700;}}
.sec-sub {{color: {MUTED}; font-size: 14px; margin: 2px 0 10px 0;}}
.ct {{font-size: 15.5px; font-weight: 650; color: {INK}; margin: 6px 0 0;}}
.cs {{font-size: 12.5px; color: {MUTED}; margin: 0 0 2px;}}
.legend-inline {{display: flex; gap: 16px; flex-wrap: wrap; font-size: 12.5px; color: {INK2}; margin: 4px 0 8px;}}
.legend-inline i {{display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 6px; vertical-align: -1px;}}
div[data-testid="stMetric"] {{background: #fff; border-radius: 12px;}}
div[data-testid="stMetricValue"] {{color: {NAVY}; font-weight: 700;}}
div[data-testid="stMetricLabel"] p {{color: {MUTED}; font-size: 13px; text-transform: uppercase; letter-spacing: .05em;}}
.stTabs [data-baseweb="tab-list"] {{gap: 4px; border-bottom: 1px solid {GRID};}}
.stTabs [data-baseweb="tab"] {{font-size: 15px; font-weight: 600; padding: 10px 16px;}}
.reco {{background: #fff; border: 1px solid {GRID}; border-top: 5px solid var(--c); border-radius: 14px; padding: 18px 20px 6px; min-height: 345px; margin-bottom: 8px;}}
.reco .tag {{display: inline-block; font-size: 11.5px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
  color: var(--c); background: var(--t); border-radius: 999px; padding: 3px 10px;}}
.reco h4 {{font-size: 20px; color: {INK}; margin: 10px 0 2px; padding: 0; line-height: 1.2;}}
.reco .why {{font-size: 13.5px; color: {MUTED}; margin: 0 0 12px;}}
.reco .kpis {{display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 10px;}}
.reco .k {{background: #F4F6FB; border-radius: 10px; padding: 9px 10px;}}
.reco .k b {{display: block; font-size: 20px; color: {NAVY};}}
.reco .k span {{font-size: 11.5px; color: {MUTED}; line-height: 1.25; display: block;}}
.reco .move {{font-size: 13.5px; color: {INK2}; border-top: 1px dashed {GRID}; padding: 10px 0 8px; margin: 0;}}
.reco .move b {{color: {INK};}}
.foot {{color: {MUTED}; font-size: 12px; margin-top: 28px; border-top: 1px solid {GRID}; padding-top: 10px;}}
</style>
"""
st.html(CSS)


# ─────────────────────────────────────────────────────────────────────────────
# Data
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading INEGI RAIAVL data…")
def load_data(path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = pd.read_excel(
        path, sheet_name="Datos",
        usecols=["ANIO", "ID_MES", "MARCA", "MODELO", "TIPO", "SEGMENTO", "PAIS_ORIGEN", "UNI_VEH"],
    )
    d = d.rename(columns={"ANIO": "year", "ID_MES": "month", "MODELO": "model", "UNI_VEH": "units"})
    d["brand"] = d["MARCA"].map(BRAND_NAME).fillna(d["MARCA"])
    d["segment"] = d["SEGMENTO"].map(SEG_EN).fillna(d["SEGMENTO"])
    d["country"] = d["PAIS_ORIGEN"].map(COUNTRY_EN).fillna(d["PAIS_ORIGEN"])
    d["type"] = d["TIPO"].map(TIPO_EN).fillna(d["TIPO"])
    d["date"] = pd.to_datetime(dict(year=d["year"], month=d["month"], day=1))
    d = d[["year", "month", "date", "brand", "model", "type", "segment", "country", "units"]]

    h = pd.read_excel(
        path, sheet_name="Datos_HEV",
        usecols=["ANIO", "ID_MES", "VEH_ELECTR", "VEH_HIBRIDAS_PLUGIN", "VEH_HIBRIDAS"],
    )
    h = h.groupby(["ANIO", "ID_MES"], as_index=False).sum()
    h.columns = ["year", "month", "Electric (BEV)", "Plug-in (PHEV)", "Hybrid (HEV)"]
    return d, h


if not DATA.exists():
    st.error(f"Data file not found. Place **{FILE}** next to app.py or in the repository root.")
    st.stop()

df, hev = load_data(str(DATA))
YEARS = sorted(df["year"].unique().tolist())
FIRST, LAST = YEARS[0], YEARS[-1]
FORD_KEY = "Ford"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def cagr(start: float, end: float, n: int) -> float:
    if n <= 0 or not start or start <= 0 or end is None or end < 0:
        return np.nan
    return (end / start) ** (1 / n) - 1


def fmt_k(v: float) -> str:
    if v is None or pd.isna(v):
        return "—"
    v = float(v)
    if abs(v) >= 1e6:
        return f"{v / 1e6:.2f}M"
    if abs(v) >= 1e4:
        return f"{v / 1e3:.0f}k"
    if abs(v) >= 1e3:
        return f"{v / 1e3:.1f}k"
    return f"{v:,.0f}"


def fmt_pct(v: float, signed: bool = True, d: int = 1) -> str:
    if v is None or pd.isna(v):
        return "—"
    return f"{v * 100:+.{d}f}%" if signed else f"{v * 100:.{d}f}%"


def section(num: str, title: str, sub: str = "") -> None:
    badge = f'<span class="num">{num}</span>' if num else ""
    st.html(f'<div class="sec">{badge}<h3>{title}</h3></div>'
            + (f'<p class="sec-sub">{sub}</p>' if sub else ""))


def chart_title(title: str, sub: str = "") -> None:
    st.html(f'<p class="ct">{title}</p>' + (f'<p class="cs">{sub}</p>' if sub else ""))


def style(fig: go.Figure, h: int = 360, legend: bool = True, hover: str = "x unified") -> go.Figure:
    fig.update_layout(
        height=h, margin=dict(l=6, r=10, t=40 if legend else 14, b=6),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family=FONT, size=13, color=INK2),
        hoverlabel=dict(bgcolor="white", bordercolor=AXIS, font=dict(family=FONT, size=12.5, color=INK)),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, xanchor="left", title=None,
                    font=dict(size=12.5), bgcolor="rgba(0,0,0,0)"),
        barcornerradius=4, bargap=0.28, hovermode=hover,
    )
    fig.update_xaxes(showgrid=False, linecolor=AXIS, tickfont=dict(color=MUTED), ticks="", title=None)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED), title=None, separatethousands=True)
    return fig


def year_axis(fig: go.Figure, a: int, b: int, step: int = 1, **kw) -> None:
    ticks = [y for y in range(a, b + 1) if (y - a) % step == 0 or y == b]
    if step > 1 and len(ticks) > 1 and ticks[-1] - ticks[-2] == 1:
        ticks.pop(-2)
    fig.update_xaxes(tickmode="array", tickvals=ticks, range=[a - 0.6, b + 0.6], tickangle=0, **kw)


def end_labels(fig: go.Figure, pts: list[tuple], h: int, ymax: float, ymin: float = 0, gap: int = 15,
               xshift: int = 24, bold: bool = False) -> None:
    """Direct labels at line ends, nudged apart so they never collide."""
    if not pts:
        return
    ppu = (h - 90) / max((ymax - ymin) * 1.06, 1e-9)
    placed = []
    for x, y, t in sorted(pts, key=lambda p: p[1]):
        py = (y - ymin) * ppu
        if placed and py - placed[-1] < gap:
            py = placed[-1] + gap
        placed.append(py)
        fig.add_annotation(x=x, y=y, text=f"<b>{t}</b>" if bold else t, showarrow=False, xshift=xshift,
                           yshift=py - (y - ymin) * ppu, font=dict(size=12, color=INK if bold else INK2))


def bands(fig: go.Figure, mode: str = "annual", labels: bool = True, **kw) -> None:
    """Shade COVID-19 (2020) and the semiconductor shortage (2021 - mid-2023)."""
    if not SHOW_BANDS:
        return
    lo, hi = Y0, Y1  # only shade the years that are on screen
    covid_on, chip_on = lo <= 2020 <= hi, lo <= 2022 and hi >= 2021
    if mode == "annual":
        spans = [(2019.5, 2020.5, "COVID-19", covid_on),
                 (max(2020.5, lo - 0.5), min(2022.5, hi + 0.5), "Chip shortage", chip_on)]
    else:
        spans = [("2020-03-01", "2020-12-31", "COVID-19", covid_on),
                 ("2021-01-01", "2023-06-30" if hi >= 2023 else f"{hi}-12-31", "Chip shortage", chip_on)]
    for (a, b, t, on), c in zip(spans, (BAND_COVID, BAND_CHIP)):
        if not on:
            continue
        extra = dict(annotation_text=t, annotation_position="top left",
                     annotation=dict(yshift=0 if t == "COVID-19" else -15, font=dict(size=11, color=MUTED))) if labels else {}
        fig.add_vrect(x0=a, x1=b, fillcolor=c, line_width=0, layer="below", **extra, **kw)


def show(fig: go.Figure, key: str | None = None) -> None:
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key=key)


def data_table(frame: pd.DataFrame, label: str = "Data table") -> None:
    with st.expander(label, icon=":material/table_chart:"):
        st.dataframe(frame, width="stretch")


def by_year(frame: pd.DataFrame) -> pd.Series:
    return frame.groupby("year")["units"].sum().reindex(YEARS, fill_value=0)


def pivot(frame: pd.DataFrame, col: str) -> pd.DataFrame:
    return frame.pivot_table(index="year", columns=col, values="units", aggfunc="sum").reindex(YEARS).fillna(0)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar: global controls
# ─────────────────────────────────────────────────────────────────────────────
def _apply_preset() -> None:
    p = st.session_state.get("preset")
    if p:
        st.session_state["period"] = PRESETS[p]


def _clear_preset() -> None:
    p = st.session_state.get("preset")
    if p and PRESETS[p] != tuple(st.session_state["period"]):
        st.session_state["preset"] = None


with st.sidebar:
    st.markdown("### :material/tune: Analysis controls")
    st.pills("Quick ranges", list(PRESETS), key="preset", on_change=_apply_preset,
             help="Jump to a pre-set window: before, during and after COVID-19 / chip shortage.")
    period = st.select_slider("Analysis period", options=YEARS, value=(FIRST, LAST), key="period",
                              on_change=_clear_preset,
                              help="Drives every chart's x-axis and every CAGR on the page.")
    SHOW_BANDS = st.toggle("Shade COVID-19 & chip shortage", value=True)
    st.html(f"""<div class="legend-inline" style="flex-direction:column;gap:6px">
      <span><i style="background:{BAND_COVID};border:1px solid {AXIS}"></i>COVID-19 · Mar–Dec 2020</span>
      <span><i style="background:{BAND_CHIP};border:1px solid {AXIS}"></i>Chip shortage · 2021–mid 2023</span></div>""")
    st.divider()
    st.caption("Source: INEGI RAIAVL, light-vehicle retail sales in Mexico, 2015–2025 (units). "
               "Hybrid/EV series start in 2016 and carry no brand detail.")

Y0, Y1 = period
if Y0 == Y1:  # a CAGR needs at least two years
    Y0, Y1 = (Y1 - 1, Y1) if Y1 > FIRST else (Y0, Y0 + 1)
N = Y1 - Y0
PER = f"{Y0}–{Y1}"

# Core aggregates
market = by_year(df)
ford_df = df[df["brand"] == FORD_KEY]
ford = by_year(ford_df)
share = ford / market
rank = df.groupby(["year", "brand"])["units"].sum().groupby(level=0).rank(ascending=False, method="min")
ford_rank = rank.xs(FORD_KEY, level="brand").reindex(YEARS)
seg_mkt = pivot(df, "segment")[[s for s in SEG_ORDER if s in df["segment"].unique()]]
seg_ford = pivot(ford_df, "segment").reindex(columns=seg_mkt.columns, fill_value=0)
tech = hev.groupby("year")[list(TECH_COL)].sum().reindex(YEARS)  # NaN for 2015
tech["Electrified"] = tech[list(TECH_COL)].sum(axis=1, min_count=1)

# ─────────────────────────────────────────────────────────────────────────────
# Hero
# ─────────────────────────────────────────────────────────────────────────────
st.html(f"""
<div class="hero">
  <div class="hero-top">
    <div>
      <div class="eyebrow">Strategy Consultant · Mexico {FIRST}-{LAST} Analysis</div>
      <h1>Ford Mexico: where to invest next</h1>
      <p class="sub">Ford's position, the market's growth, and how buyers are shifting</p>
    </div>
    {f'<img class="hero-logo" src="{LOGO_SRC}" alt="Ford logo">' if LOGO_SRC else ""}
  </div>
  <div class="hero-stats">
    <div class="hero-stat"><div class="lbl">Ford units {LAST}</div><div class="val">{fmt_k(ford[LAST])} <small>vs {fmt_k(ford[FIRST])} in {FIRST}</small></div></div>
    <div class="hero-stat"><div class="lbl">Market share</div><div class="val">{share[LAST]*100:.1f}% <small>from {share[FIRST]*100:.1f}%</small></div></div>
    <div class="hero-stat"><div class="lbl">Brand rank</div><div class="val">#{ford_rank[LAST]:.0f} <small>from #{ford_rank[FIRST]:.0f}</small></div></div>
    <div class="hero-stat"><div class="lbl">Market {LAST}</div><div class="val">{fmt_k(market[LAST])} <small>{fmt_pct(cagr(market[FIRST], market[LAST], LAST-FIRST))} CAGR</small></div></div>
  </div>
</div>""")

t1, t2, t3, t4 = st.tabs([
    ":material/directions_car: 01 · Ford today",
    ":material/factory: 02 · Industry",
    ":material/groups: 03 · Customer preferences",
    ":material/flag: Recommendations",
])

# ═════════════════════════════════════════════════════════════════════════════
# 01 · FORD TODAY
# ═════════════════════════════════════════════════════════════════════════════
with t1:
    section("01", "Ford today", f"Units sold in Mexico · {PER}")

    c = st.columns(4)
    c[0].metric(f"Units {Y1}", fmt_k(ford[Y1]), fmt_pct(ford[Y1] / ford[Y1 - 1] - 1) + f" vs {Y1-1}" if Y1 > FIRST else None, border=True)
    c[1].metric(f"CAGR {PER}", fmt_pct(cagr(ford[Y0], ford[Y1], N)),
                f"Market {fmt_pct(cagr(market[Y0], market[Y1], N))}", delta_color="off", delta_arrow="off", border=True)
    c[2].metric(f"Market share {Y1}", f"{share[Y1]*100:.1f}%", f"{(share[Y1]-share[Y0])*100:+.1f} pp vs {Y0}", border=True)
    c[3].metric(f"Brand rank {Y1}", f"#{ford_rank[Y1]:.0f}", f"{ford_rank[Y0]-ford_rank[Y1]:+.0f} places vs {Y0}", border=True)

    # 1.1 Units by year + share
    yrs = list(range(Y0, Y1 + 1))
    a, b = st.columns([3, 2], gap="large")
    with a:
        chart_title("Units sold by year", "Ford Motor, all segments")
        s = ford.loc[yrs]
        lbl_years = {Y0, Y1, int(s.idxmax()), int(s.idxmin())}
        fig = go.Figure(go.Bar(
            x=yrs, y=s.values, marker_color=FORD, name="Ford",
            text=[fmt_k(v) if y in lbl_years else "" for y, v in zip(yrs, s.values)],
            textposition="outside", textfont=dict(color=INK2, size=12), cliponaxis=False,
            hovertemplate="%{x}: %{y:,.0f} units<extra></extra>",
        ))
        style(fig, 340, legend=False, hover="closest"); year_axis(fig, Y0, Y1); bands(fig)
        fig.update_yaxes(range=[0, s.max() * 1.18])
        show(fig)
    with b:
        chart_title("Market share", "Ford units ÷ total market")
        sh = share.loc[yrs] * 100
        fig = go.Figure(go.Scatter(
            x=yrs, y=sh.values, mode="lines+markers", line=dict(color=FORD, width=2.5),
            marker=dict(size=8, color=FORD, line=dict(color="white", width=2)), name="Share",
            hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
        ))
        for y in (Y0, Y1):
            fig.add_annotation(x=y, y=sh[y], text=f"<b>{sh[y]:.1f}%</b>", showarrow=False, yshift=16,
                               font=dict(color=INK, size=12.5))
        style(fig, 340, legend=False, hover="closest"); year_axis(fig, Y0, Y1, step=2 if N > 6 else 1); bands(fig)
        fig.update_yaxes(ticksuffix="%", range=[0, max(sh.max() * 1.25, 1)])
        show(fig)

    # 1.2 Segment mix
    a, b = st.columns([3, 2], gap="large")
    with a:
        head_l, head_r = st.columns([3, 2])
        with head_l:
            chart_title("Units by car segment", "Ford exited cars; volume now rests on SUVs and pickups")
        with head_r:
            mode = st.segmented_control("View", ["Units", "% mix"], default="Units", key="ford_seg_mode",
                                        label_visibility="collapsed")
        sf = seg_ford.loc[yrs]
        sf = sf.loc[:, sf.sum() > 0]
        vals = sf.div(sf.sum(axis=1), axis=0) * 100 if mode == "% mix" else sf
        fig = go.Figure()
        for sname in [s for s in SEG_ORDER if s in vals.columns]:
            fig.add_bar(x=yrs, y=vals[sname], name=sname, marker=dict(color=SEG_COL[sname], line=dict(color="white", width=1.5)),
                        hovertemplate=f"{sname}: " + ("%{y:.1f}%" if mode == "% mix" else "%{y:,.0f}") + "<extra></extra>")
        style(fig, 380); fig.update_layout(barmode="stack", legend_traceorder="normal"); year_axis(fig, Y0, Y1); bands(fig, labels=False)
        if mode == "% mix":
            fig.update_yaxes(ticksuffix="%", range=[0, 100])
        show(fig)
    with b:
        head_l, head_r = st.columns([3, 2])
        with head_r:
            top_year = st.selectbox("Year", yrs[::-1], index=0, key="top_year", label_visibility="collapsed")
        with head_l:
            chart_title(f"Top nameplates · {top_year}", "Units, colored by segment")
        top = (ford_df[ford_df["year"] == top_year].groupby(["model", "segment"])["units"].sum()
               .reset_index().sort_values("units", ascending=False).head(10).iloc[::-1])
        fig = go.Figure(go.Bar(
            x=top["units"], y=top["model"], orientation="h",
            marker_color=[SEG_COL.get(s, CONTEXT) for s in top["segment"]],
            text=[fmt_k(v) for v in top["units"]], textposition="outside", cliponaxis=False,
            textfont=dict(color=INK2, size=12), customdata=top["segment"],
            hovertemplate="%{y} · %{customdata}: %{x:,.0f}<extra></extra>",
        ))
        style(fig, 380, legend=False, hover="closest")
        fig.update_xaxes(showticklabels=False, showgrid=False, range=[0, top["units"].max() * 1.2] if len(top) else None)
        fig.update_yaxes(showgrid=False, tickfont=dict(color=INK2, size=12.5))
        show(fig)

    # 1.3 Country of origin
    chart_title("Where Ford's Mexico sales are built", f"Units by country of manufacture · {PER}")
    CO_SHOW = {"United States": "#1F4FB8", "Mexico": "#12A0B0", "China": "#D98E04", "Argentina": "#C2508F"}
    co = pivot(ford_df, "country").reindex(columns=list(CO_SHOW), fill_value=0).loc[yrs]
    fig = go.Figure()
    for cname, col in CO_SHOW.items():
        fig.add_scatter(x=yrs, y=co[cname].values, name=cname, mode="lines+markers", line=dict(color=col, width=2.5),
                        marker=dict(size=7, color=col, line=dict(color="white", width=1.5)),
                        hovertemplate=f"{cname}: %{{y:,.0f}}<extra></extra>")
    end_labels(fig, [(Y1, co.loc[Y1, c], fmt_k(co.loc[Y1, c])) for c in CO_SHOW], 380, co.max().max(), xshift=26)
    style(fig, 380); fig.update_layout(legend=dict(traceorder="normal"))
    year_axis(fig, Y0, Y1); bands(fig)
    fig.update_xaxes(range=[Y0 - 0.4, Y1 + 0.9]); fig.update_yaxes(rangemode="tozero")
    show(fig)
    co_all = pivot(ford_df, "country").loc[yrs]
    hidden = [c for c in co_all.columns[co_all.sum() > 0] if c not in CO_SHOW]
    if hidden:
        st.caption(f"Not shown: {', '.join(sorted(hidden))} "
                   f"({fmt_k(co_all[hidden].sum().sum())} units over {PER}).")

    data_table(pd.DataFrame({"Ford units": ford, "Market units": market, "Share %": (share * 100).round(2),
                             "Rank": ford_rank}).join(seg_ford.add_prefix("Ford · ")).loc[Y0:Y1].astype(float).round(2))

# ═════════════════════════════════════════════════════════════════════════════
# 02 · INDUSTRY
# ═════════════════════════════════════════════════════════════════════════════
with t2:
    section("02", "Automotive industry", f"Total Mexican light-vehicle market · {PER}")

    seg_cagr = pd.Series({s: cagr(seg_mkt.loc[Y0, s], seg_mkt.loc[Y1, s], N) for s in seg_mkt.columns})
    mkt_cagr = cagr(market[Y0], market[Y1], N)
    fastest = seg_cagr.dropna().idxmax()

    c = st.columns(4)
    c[0].metric(f"Market {Y1}", fmt_k(market[Y1]), fmt_pct(market[Y1] / market[Y1 - 1] - 1) + f" vs {Y1-1}" if Y1 > FIRST else None, border=True)
    c[1].metric(f"Market CAGR {PER}", fmt_pct(mkt_cagr), border=True)
    c[2].metric(f"{Y1} vs pre-COVID 2019", f"{market[Y1] / market[2019] * 100:.0f}%", "of 2019 volume", delta_color="off", delta_arrow="off", border=True)
    c[3].metric("Fastest-growing segment", fastest, f"{fmt_pct(seg_cagr[fastest])} CAGR", border=True)

    # 2.1 Total market
    with st.container():
        hl, hr = st.columns([3, 2])
        with hl:
            back = next((y for y in YEARS if y > 2020 and market[y] >= market[2019]), None)
            chart_title("Total market units", f"COVID cut 2020 volume {abs(market[2020] / market[2019] - 1) * 100:.0f}% vs 2019"
                        + (f"; back above 2019 in {back}" if back else ""))
        with hr:
            view = st.segmented_control("View", ["Full market", "By segment"], default="Full market", key="mkt_view",
                                        label_visibility="collapsed")
        s = market.loc[yrs]
        if view == "By segment":
            fig = go.Figure()
            for sname in seg_mkt.columns:
                fig.add_bar(x=yrs, y=seg_mkt.loc[yrs, sname], name=sname,
                            marker=dict(color=SEG_COL[sname], line=dict(color="white", width=1.5)),
                            hovertemplate=f"{sname}: %{{y:,.0f}}<extra></extra>")
            # market total above each stack, same as the full-market view
            fig.add_scatter(x=yrs, y=s.values, mode="text", text=[fmt_k(v) for v in s.values], textposition="top center",
                            textfont=dict(color=INK2, size=11.5), showlegend=False, hoverinfo="skip", cliponaxis=False)
            style(fig, 400); fig.update_layout(barmode="stack", legend_traceorder="normal")
            year_axis(fig, Y0, Y1); bands(fig, labels=False)
        else:
            fig = go.Figure(go.Bar(
                x=yrs, y=s.values, marker_color=FORD, name="Market",
                text=[fmt_k(v) for v in s.values], textposition="outside", cliponaxis=False,
                textfont=dict(color=INK2, size=11.5), hovertemplate="%{x}: %{y:,.0f} units<extra></extra>",
            ))
            style(fig, 400, legend=False, hover="closest"); year_axis(fig, Y0, Y1); bands(fig)
        fig.update_yaxes(range=[0, s.max() * 1.15])
        show(fig)
    # 2.3 One-vs-one comparison
    section("1v1", "Head-to-head comparison", "Pick any two companies")
    brand_rank = df[(df["year"] >= Y0) & (df["year"] <= Y1)].groupby("brand")["units"].sum().sort_values(ascending=False)
    brands = brand_rank.index.tolist()
    cc = st.columns([1, 1, 2])
    A = cc[0].selectbox("Company A", brands, index=brands.index(FORD_KEY) if FORD_KEY in brands else 0)
    others = [x for x in brands if x != A]
    B = cc[1].selectbox("Company B", others, index=others.index("Toyota") if "Toyota" in others else 0)
    dA, dB = df[df["brand"] == A], df[df["brand"] == B]
    segA, segB = pivot(dA, "segment"), pivot(dB, "segment")
    used = [s for s in SEG_ORDER if (s in segA and segA.loc[Y0:Y1, s].sum() > 0) or (s in segB and segB.loc[Y0:Y1, s].sum() > 0)]
    seg = cc[2].selectbox("Car segment", used, index=used.index("SUVs") if "SUVs" in used else 0,
                          key="cmp_seg") if used else None
    segs = [seg] if seg else []
    COL_A, COL_B = FORD, RIVAL

    uA, uB = by_year(dA), by_year(dB)
    k = st.columns(4)
    k[0].metric(f"{A} · {Y1}", fmt_k(uA[Y1]), f"CAGR {fmt_pct(cagr(uA[Y0], uA[Y1], N))}", delta_color="off", delta_arrow="off", border=True)
    k[1].metric(f"{B} · {Y1}", fmt_k(uB[Y1]), f"CAGR {fmt_pct(cagr(uB[Y0], uB[Y1], N))}", delta_color="off", delta_arrow="off", border=True)
    k[2].metric(f"Share {Y1}: {A}", f"{uA[Y1] / market[Y1] * 100:.1f}%", f"{(uA[Y1]/market[Y1]-uA[Y0]/market[Y0])*100:+.1f} pp vs {Y0}", border=True)
    k[3].metric(f"Share {Y1}: {B}", f"{uB[Y1] / market[Y1] * 100:.1f}%", f"{(uB[Y1]/market[Y1]-uB[Y0]/market[Y0])*100:+.1f} pp vs {Y0}", border=True)

    a, b = st.columns(2, gap="large")
    with a:
        chart_title("Total units sold by year", f"{A} vs {B}")
        fig = go.Figure()
        for name, ser, col in ((A, uA, COL_A), (B, uB, COL_B)):
            s = ser.loc[yrs]
            fig.add_scatter(x=yrs, y=s.values, name=name, mode="lines+markers", line=dict(color=col, width=2.5),
                            marker=dict(size=8, color=col, line=dict(color="white", width=2)),
                            hovertemplate=f"{name}: %{{y:,.0f}}<extra></extra>")
        end_labels(fig, [(Y1, uA[Y1], fmt_k(uA[Y1])), (Y1, uB[Y1], fmt_k(uB[Y1]))], 420,
                   max(uA.loc[yrs].max(), uB.loc[yrs].max()), xshift=26, bold=True)
        style(fig, 420); year_axis(fig, Y0, Y1, step=2 if N > 6 else 1); bands(fig)
        fig.update_xaxes(range=[Y0 - 0.4, Y1 + 0.9]); fig.update_yaxes(rangemode="tozero")
        show(fig)
    with b:
        chart_title(f"Units by car segment by year · {seg or '—'}", f"{A} vs {B}")
        if not seg:
            st.info("Neither company sold in any segment during this period.")
        else:
            fig = go.Figure()
            ends, top = [], 0
            for name, sp, col in ((A, segA, COL_A), (B, segB, COL_B)):
                s = sp[seg].loc[yrs] if seg in sp else pd.Series(0, index=yrs)
                fig.add_scatter(x=yrs, y=s.values, name=name, mode="lines+markers", line=dict(color=col, width=2.5),
                                marker=dict(size=8, color=col, line=dict(color="white", width=2)),
                                hovertemplate=f"{name} · {seg}: %{{y:,.0f}}<extra></extra>")
                ends.append((Y1, s[Y1], fmt_k(s[Y1])))
                top = max(top, s.max())
            end_labels(fig, ends, 420, top, xshift=26, bold=True)
            style(fig, 420); year_axis(fig, Y0, Y1, step=2 if N > 6 else 1); bands(fig)
            fig.update_xaxes(range=[Y0 - 0.4, Y1 + 0.9]); fig.update_yaxes(rangemode="tozero")
            show(fig)

    cmp = pd.DataFrame({A: uA, B: uB}).loc[Y0:Y1]
    data_table(cmp.join(segA.reindex(columns=segs).add_prefix(f"{A} · ")).join(segB.reindex(columns=segs).add_prefix(f"{B} · ")).fillna(0).astype(int))

# ═════════════════════════════════════════════════════════════════════════════
# 03 · CUSTOMER PREFERENCES
# ═════════════════════════════════════════════════════════════════════════════
with t3:
    section("03", "Customer preferences", f"How Mexican buyers' choices shifted · {PER}")

    mix = seg_mkt.div(market, axis=0) * 100
    car_share = (mix["Subcompact"] + mix["Compact"])
    hev_y0 = max(Y0, 2016)
    hev_cagr = cagr(tech.loc[hev_y0, "Hybrid (HEV)"], tech.loc[Y1, "Hybrid (HEV)"], Y1 - hev_y0)
    mv_cagr = cagr(seg_mkt.loc[Y0, "Minivans"], seg_mkt.loc[Y1, "Minivans"], N)

    c = st.columns(4)
    c[0].metric(f"SUV share {Y1}", f"{mix.loc[Y1, 'SUVs']:.0f}%", f"{mix.loc[Y1,'SUVs']-mix.loc[Y0,'SUVs']:+.1f} pp vs {Y0}", border=True)
    c[1].metric(f"Compact + subcompact {Y1}", f"{car_share[Y1]:.0f}%", f"{car_share[Y1]-car_share[Y0]:+.1f} pp vs {Y0}", border=True)
    c[2].metric(f"Minivan CAGR {PER}", fmt_pct(mv_cagr), f"{fmt_k(seg_mkt.loc[Y1,'Minivans'])} units in {Y1}", delta_color="off", delta_arrow="off", border=True)
    c[3].metric(f"Hybrid CAGR {hev_y0}–{Y1}", fmt_pct(hev_cagr), f"{fmt_k(tech.loc[Y1,'Hybrid (HEV)'])} units in {Y1}", delta_color="off", delta_arrow="off", border=True)

    # 3.1 Segment growth
    a, b = st.columns([2, 3], gap="large")
    with a:
        chart_title(f"CAGR by segment · {PER}", "Dashed line = total market")
        sc = seg_cagr.sort_values()
        fig = go.Figure(go.Bar(
            x=sc.values * 100, y=sc.index, orientation="h",
            marker_color=[POS if v >= 0 else NEG for v in sc.values],
            text=[fmt_pct(v) for v in sc.values], textposition="outside", cliponaxis=False,
            textfont=dict(color=INK2, size=12), hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
        ))
        fig.add_vline(x=mkt_cagr * 100, line=dict(color=INK2, width=1.5, dash="dash"),
                      annotation_text=f"Market {fmt_pct(mkt_cagr)}", annotation_position="top",
                      annotation_font=dict(size=11.5, color=INK2))
        style(fig, 360, legend=False, hover="closest")
        span = np.nanmax(np.abs(sc.values * 100)) if sc.notna().any() else 10
        fig.update_xaxes(ticksuffix="%", showgrid=True, gridcolor=GRID, zeroline=True, zerolinecolor=AXIS,
                         range=[min(-2, np.nanmin(sc.values * 100) * 1.35), span * 1.35])
        fig.update_yaxes(showgrid=False, tickfont=dict(color=INK2, size=12.5))
        show(fig)

    with b:
        chart_title("Segment CAGR across the cycle", "How each segment behaved before, during and after the shocks")
        windows = {"Pre-COVID<br>2015–19": (2015, 2019), "COVID + chips<br>2019–22": (2019, 2022),
                   "Recovery<br>2022–25": (2022, 2025), "Decade<br>2015–25": (2015, 2025)}
        rows = list(seg_mkt.columns) + ["Total market"]
        z = []
        for sname in rows:
            ser = market if sname == "Total market" else seg_mkt[sname]
            z.append([cagr(ser[w0], ser[w1], w1 - w0) * 100 for w0, w1 in windows.values()])
        z = np.array(z, dtype=float)
        lim = np.nanmax(np.abs(np.clip(z, -40, 40)))
        fig = go.Figure(go.Heatmap(
            z=np.clip(z, -lim, lim), x=list(windows), y=rows, zmid=0, zmin=-lim, zmax=lim,
            colorscale=[[0, NEG], [0.5, "#F2F3F6"], [1, POS]], showscale=False, xgap=3, ygap=3,
            text=[[("—" if np.isnan(v) else f"{v:+.1f}%") for v in r] for r in z], texttemplate="%{text}",
            textfont=dict(size=13, family=FONT), customdata=z,
            hovertemplate="%{y} · %{x}: %{customdata:.1f}%<extra></extra>",
        ))
        style(fig, 360, legend=False, hover="closest")
        fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(color=INK2, size=12.5))
        fig.update_xaxes(side="top", tickfont=dict(color=INK2, size=12))
        show(fig)

    # 3.2 Emerging segments
    section("", "Emerging segments", "Minivans and hybrids are the fastest-growing pockets of demand")
    series = {
        "Minivans": seg_mkt["Minivans"], "Hybrid (HEV)": tech["Hybrid (HEV)"], "Plug-in (PHEV)": tech["Plug-in (PHEV)"],
        "Electric (BEV)": tech["Electric (BEV)"], "SUVs": seg_mkt["SUVs"], "Sports": seg_mkt["Sports"],
        "Pickups": seg_mkt["Pickups"], "Total market": market,
    }
    EM_COL = {"Minivans": SEG_COL["Minivans"], "Hybrid (HEV)": TECH_COL["Hybrid (HEV)"], "Plug-in (PHEV)": TECH_COL["Plug-in (PHEV)"],
              "Electric (BEV)": TECH_COL["Electric (BEV)"], "SUVs": SEG_COL["SUVs"], "Sports": SEG_COL["Sports"],
              "Pickups": SEG_COL["Pickups"], "Total market": INK2}
    base = max(Y0, 2016) if Y0 < 2016 else Y0
    a, b = st.columns([3, 2], gap="large")
    with a:
        chart_title(f"Growth index · {base} = 100", "Hybrid/EV data start in 2016, so the index starts there when needed")
        em_pick = st.pills("Series", list(series), default=["Minivans", "Hybrid (HEV)", "SUVs", "Total market"],
                           selection_mode="multi", key="em_pick", label_visibility="collapsed")
        fig = go.Figure()
        iyrs = list(range(base, Y1 + 1))
        ends, top_idx = [], 100
        for name in [n for n in series if n in (em_pick or [])]:
            s = series[name].loc[iyrs]
            if not s.iloc[0] or pd.isna(s.iloc[0]):
                continue
            idx = s / s.iloc[0] * 100
            dash = "dot" if name == "Total market" else "solid"
            fig.add_scatter(x=iyrs, y=idx.values, name=name, mode="lines+markers",
                            line=dict(color=EM_COL[name], width=2.5, dash=dash),
                            marker=dict(size=7, color=EM_COL[name], line=dict(color="white", width=1.5)),
                            hovertemplate=f"{name}: %{{y:.0f}}<extra></extra>")
            ends.append((Y1, idx.iloc[-1], f"{idx.iloc[-1]:.0f}"))
            top_idx = max(top_idx, idx.max())
        end_labels(fig, ends, 400, top_idx, xshift=22)
        fig.add_hline(y=100, line=dict(color=AXIS, width=1))
        style(fig, 400); year_axis(fig, base, Y1); bands(fig)
        fig.update_xaxes(range=[base - 0.4, Y1 + 0.8])
        show(fig)
    with b:
        chart_title(f"CAGR · {base}–{Y1}", "Same window for every series")
        cg = pd.Series({n: cagr(s.loc[base], s.loc[Y1], Y1 - base) for n, s in series.items()}).dropna().sort_values()
        fig = go.Figure(go.Bar(
            x=cg.values * 100, y=cg.index, orientation="h",
            marker_color=[EM_COL[n] if n != "Total market" else CONTEXT for n in cg.index],
            text=[fmt_pct(v) for v in cg.values], textposition="outside", cliponaxis=False,
            textfont=dict(color=INK2, size=12), hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
        ))
        style(fig, 400 + 38, legend=False, hover="closest")
        fig.update_xaxes(ticksuffix="%", showgrid=True, gridcolor=GRID, zeroline=True, zerolinecolor=AXIS,
                         range=[min(cg.min() * 140, -cg.max() * 18), cg.max() * 135 if len(cg) else 10])
        fig.update_yaxes(showgrid=False, tickfont=dict(color=INK2, size=12.5))
        show(fig)

    # 3.3 Electrification
    a, b = st.columns([3, 2], gap="large")
    eyrs = [y for y in yrs if y >= 2016]
    with a:
        chart_title("Electrified sales by technology", "Units sold by EV segment")
        fig = go.Figure()
        for tname, col in TECH_COL.items():
            fig.add_bar(x=eyrs, y=tech.loc[eyrs, tname], name=tname, marker=dict(color=col, line=dict(color="white", width=1.5)),
                        hovertemplate=f"{tname}: %{{y:,.0f}}<extra></extra>")
        tot = tech.loc[eyrs, "Electrified"]
        fig.add_scatter(x=eyrs, y=tot * 1.04, mode="text", text=[fmt_k(v) for v in tot], textposition="top center",
                        textfont=dict(size=11.5, color=INK2), showlegend=False, hoverinfo="skip")
        style(fig, 360); fig.update_layout(barmode="stack", legend_traceorder="normal")
        if eyrs:
            year_axis(fig, eyrs[0], eyrs[-1]); fig.update_yaxes(range=[0, tot.max() * 1.18])
        bands(fig, labels=False)
        show(fig)
    with b:
        chart_title("Electrified penetration", "Share of total market")
        pen = (tech.loc[eyrs, ["Hybrid (HEV)", "Electrified"]].div(market.loc[eyrs], axis=0) * 100)
        fig = go.Figure()
        fig.add_scatter(x=eyrs, y=pen["Electrified"], name="All electrified", mode="lines+markers",
                        line=dict(color=TECH_COL["Plug-in (PHEV)"], width=2.5), marker=dict(size=7),
                        hovertemplate="All electrified: %{y:.1f}%<extra></extra>")
        fig.add_scatter(x=eyrs, y=pen["Hybrid (HEV)"], name="Hybrid (HEV)", mode="lines+markers",
                        line=dict(color=TECH_COL["Hybrid (HEV)"], width=2.5), marker=dict(size=7),
                        hovertemplate="HEV: %{y:.1f}%<extra></extra>")
        if eyrs:
            fig.add_annotation(x=eyrs[-1], y=pen["Electrified"].iloc[-1], text=f"<b>{pen['Electrified'].iloc[-1]:.1f}%</b>",
                               showarrow=False, yshift=14, font=dict(size=12, color=INK))
            year_axis(fig, eyrs[0], eyrs[-1], step=2 if len(eyrs) > 7 else 1)
        style(fig, 360); bands(fig, labels=False)
        fig.update_yaxes(ticksuffix="%", rangemode="tozero")
        show(fig)
    data_table(pd.concat([mix.round(1).add_suffix(" share %"), tech.drop(columns="Electrified")], axis=1).loc[Y0:Y1])

# ═════════════════════════════════════════════════════════════════════════════
# RECOMMENDATIONS
# ═════════════════════════════════════════════════════════════════════════════
with t4:
    section("→", "Where Ford should invest", f"Segment attractiveness vs Ford's position · growth {PER}, share {Y1}")

    # Where-to-play matrix
    seg_tbl = pd.DataFrame({
        "cagr": seg_cagr * 100,
        "ford_share": (seg_ford.loc[Y1] / seg_mkt.loc[Y1].replace(0, np.nan)) * 100,
        "units": seg_mkt.loc[Y1],
    }).dropna(subset=["cagr"])
    x_ref, y_ref = mkt_cagr * 100, share[Y1] * 100
    fig = go.Figure()
    for sname, r in seg_tbl.iterrows():
        fig.add_scatter(
            x=[r["cagr"]], y=[r["ford_share"]], mode="markers+text", name=sname, text=[f"<b>{sname}</b>"],
            textposition="top center", textfont=dict(size=12.5, color=INK),
            marker=dict(size=max(14, np.sqrt(r["units"]) / 8.5), color=SEG_COL.get(sname, CONTEXT), opacity=0.85,
                        line=dict(color="white", width=2)),
            customdata=[[r["units"]]],
            hovertemplate=f"<b>{sname}</b><br>CAGR %{{x:.1f}}%<br>Ford share %{{y:.1f}}%<br>Segment {Y1}: %{{customdata[0]:,.0f}} units<extra></extra>",
        )
    fig.add_vline(x=x_ref, line=dict(color=AXIS, width=1.5, dash="dash"))
    fig.add_hline(y=y_ref, line=dict(color=AXIS, width=1.5, dash="dash"))
    xr = [min(seg_tbl["cagr"].min(), x_ref) - 4, max(seg_tbl["cagr"].max(), x_ref) + 5]
    yr = [-1.5, max(seg_tbl["ford_share"].max(), y_ref) * 1.35 + 1]
    for txt, xx, yy, xa, ya in (("GROW & DEFEND", xr[1], yr[1], "right", "top"), ("INVEST TO ENTER", xr[1], yr[0], "right", "bottom"),
                                ("HARVEST", xr[0], yr[1], "left", "top"), ("DEPRIORITIZE", xr[0], yr[0], "left", "bottom")):
        fig.add_annotation(x=xx, y=yy, text=txt, showarrow=False, xanchor=xa, yanchor=ya,
                           font=dict(size=11.5, color=MUTED, family=FONT))
    style(fig, 430, legend=False, hover="closest")
    fig.update_xaxes(title=dict(text=f"Segment CAGR {PER} →", font=dict(size=12.5, color=MUTED)), ticksuffix="%",
                     showgrid=True, gridcolor=GRID, range=xr, zeroline=False)
    fig.update_yaxes(title=dict(text=f"Ford share of segment {Y1} →", font=dict(size=12.5, color=MUTED)), ticksuffix="%", range=yr)
    fig.add_annotation(x=x_ref, y=yr[1], text=f"Market {fmt_pct(mkt_cagr)}", showarrow=False, yanchor="top", xshift=46,
                       font=dict(size=11, color=MUTED))
    fig.add_annotation(x=xr[0], y=y_ref, text=f"Ford avg {y_ref:.1f}%", showarrow=False, xanchor="left", yshift=10,
                       font=dict(size=11, color=MUTED))
    show(fig)
    st.caption("Bubble size = segment units. Hybrids are a powertrain, not a segment, so they sit inside these bubbles.")

    # Evidence (latest year, fixed windows so the recommendations stay stable)
    L, P5 = LAST, LAST - 5
    mv_tot = seg_mkt.loc[L, "Minivans"]
    mv_c10 = cagr(seg_mkt.loc[FIRST, "Minivans"], mv_tot, L - FIRST)
    mv_c5 = cagr(seg_mkt.loc[P5, "Minivans"], mv_tot, 5)
    ford_mv = seg_ford.loc[L, "Minivans"]
    terr = ford_df[(ford_df["model"] == "Territory")].groupby("year")["units"].sum().reindex(YEARS, fill_value=0)
    hev_L = tech.loc[L, "Hybrid (HEV)"]
    hev_c = cagr(tech.loc[2016, "Hybrid (HEV)"], hev_L, L - 2016)
    ford_hyb = ford_df[ford_df["model"].str.contains("HEV|Hibrid|Hybrid", case=False, regex=True)].groupby("year")["units"].sum().reindex(YEARS, fill_value=0)
    sp_c5 = cagr(seg_mkt.loc[P5, "Sports"], seg_mkt.loc[L, "Sports"], 5)
    vw_seat = df[(df["year"] == L) & (((df["brand"] == "Volkswagen") & (df["model"] == "GTI")) |
                                      ((df["brand"] == "SEAT") & (df["model"] == "Leon")))]["units"].sum()
    mustang = ford_df[(ford_df["year"] == L) & (ford_df["model"] == "Mustang")]["units"].sum()

    def reco_card(n: int, tag: str, color: str, tint: str, title: str, why: str, kpis: list[tuple[str, str]], move: str) -> None:
        k = "".join(f'<div class="k"><b>{v}</b><span>{lbl}</span></div>' for v, lbl in kpis)
        st.html(f"""<div class="reco" style="--c:{color};--t:{tint}">
          <span class="tag">{n:02d} · {tag}</span><h4>{title}</h4><p class="why">{why}</p>
          <div class="kpis">{k}</div><p class="move"><b>The move:</b> {move}</p></div>""")

    def leader_chart(frame: pd.DataFrame, highlight: dict[str, str], h: int = 250) -> None:
        frame = frame.iloc[::-1]
        cols = [next((c for key, c in highlight.items() if key in lbl), CONTEXT) for lbl in frame.index]
        fig = go.Figure(go.Bar(
            x=frame.values, y=frame.index, orientation="h", marker_color=cols,
            text=[fmt_k(v) for v in frame.values], textposition="outside", cliponaxis=False,
            textfont=dict(size=11.5, color=INK2), hovertemplate="%{y}: %{x:,.0f}<extra></extra>",
        ))
        style(fig, h, legend=False, hover="closest")
        fig.update_layout(margin=dict(l=4, r=30, t=8, b=4))
        fig.update_xaxes(showticklabels=False, range=[0, frame.max() * 1.25])
        fig.update_yaxes(showgrid=False, tickfont=dict(size=11.5, color=INK2))
        show(fig)

    def seg_leaders(seg: str, n: int = 6) -> pd.Series:
        x = df[(df["year"] == L) & (df["segment"] == seg)].copy()
        x["label"] = x["model"] + " · " + x["brand"].str.split(" ").str[0]
        lead = x.groupby("label")["units"].sum().sort_values(ascending=False)
        top = lead.head(n)
        ford_rows = lead[lead.index.str.endswith("· Ford")]
        if len(ford_rows) and not top.index.str.endswith("· Ford").any():
            top = pd.concat([top.head(n - 1), ford_rows.head(1)])
        return top

    r1, r2, r3 = st.columns(3, gap="medium")
    with r1:
        reco_card(1, "Growth bet", "#B37400", "#FDF1DC", "New minivan, with a hybrid option",
                  "Fastest-growing segment; Ford has no true minivan.",
                  [(fmt_pct(mv_c5, d=0), f"Minivan CAGR {P5}–{L}"), (fmt_k(mv_tot), f"Segment units {L}"),
                   (f"{ford_mv / mv_tot * 100:.1f}%", f"Ford share {L} (Expedition)")],
                  "Family minivan with HEV trim, sourced from Ford's global van platforms; target Sienna buyers.")
        chart_title(f"Minivan leaders · {L}")
        leader_chart(seg_leaders("Minivans"), {"Ford": FORD, "Sienna": RIVAL})
    with r2:
        reco_card(2, "Quick win", FORD, "#E4ECFB", "Extend Territory with hybrid trims",
                  "Territory is Ford's #1 nameplate; hybrids are the volume EV tech.",
                  [(fmt_k(terr[L]), f"Territory units {L} ({terr[L] / ford[L] * 100:.0f}% of Ford)"),
                   (fmt_pct(hev_c, d=0), f"Hybrid CAGR 2016–{L}"),
                   (f"{ford_hyb[L] / hev_L * 100:.1f}%", f"Ford share of hybrids {L}")],
                  "Add HEV/PHEV Territory from the China line-up; protect the nameplate as Chinese brands scale.")
        chart_title("Territory units by year")
        ty = [y for y in YEARS if y >= 2022]
        fig = go.Figure(go.Bar(x=ty, y=terr.loc[ty], marker_color=FORD, text=[fmt_k(v) for v in terr.loc[ty]],
                               textposition="outside", cliponaxis=False, textfont=dict(size=11.5, color=INK2),
                               hovertemplate="%{x}: %{y:,.0f}<extra></extra>"))
        style(fig, 250, legend=False, hover="closest"); year_axis(fig, ty[0], ty[-1])
        fig.update_layout(margin=dict(l=4, r=4, t=8, b=4)); fig.update_yaxes(showticklabels=False, range=[0, terr.max() * 1.25])
        show(fig)
    with r3:
        reco_card(3, "Brand halo", NEG, "#FBE6E4", "Sport compact vs GTI & León",
                  "Sports demand is recovering; VW group owns the affordable hot-hatch.",
                  [(fmt_pct(sp_c5, d=0), f"Sports CAGR {P5}–{L}"), (fmt_k(vw_seat), f"GTI + León units {L}"),
                   (fmt_k(mustang), f"Mustang units {L}")],
                  "A sub-Mustang performance compact (ST badge) to win younger buyers and lift brand heat.")
        chart_title(f"Sports leaders · {L}")
        leader_chart(seg_leaders("Sports"), {"Ford": FORD, "GTI": RIVAL, "Leon": RIVAL})

    st.html(f"""<div class="legend-inline" style="margin-top:6px">
      <span><i style="background:{FORD}"></i>Ford</span><span><i style="background:{RIVAL}"></i>Key rival</span>
      <span><i style="background:{CONTEXT}"></i>Other models</span></div>""")

st.html(f"""<div class="foot">Source: INEGI · Registro Administrativo de la Industria Automotriz de Vehículos Ligeros (RAIAVL),
retail sales {FIRST}–{LAST}. BYD, Tesla and other non-reporting brands are excluded, so EV volumes are understated.
INEGI segments are used as reported (e.g. Expedition is classified as a minivan). Country = country of manufacture.</div>""")
