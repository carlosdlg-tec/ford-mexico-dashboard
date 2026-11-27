# Ford Mexico · Where to invest next

Streamlit dashboard for a strategy review of Ford in the Mexican light-vehicle market (INEGI RAIAVL retail sales, 2015–2025).

| Tab | What it shows |
|---|---|
| **01 · Ford today** | Units by year, market share, units by car segment (units / % mix), top 10 nameplates for a year you pick from a dropdown, and units by country of manufacture (United States, Mexico, China, Argentina) as a line chart, with a Mexico vs China view that bolds Mexico's first-year and both countries' latest-year units; a note lists the countries not shown |
| **02 · Industry** | Total market units by year, with a one-click switch between the full market and a stacked split by car segment, plus a **head-to-head comparison** of any two companies, or of one company against all Chinese brands combined: side-by-side, equal-width charts of total units by year and units by year for one car segment picked from a dropdown |
| **03 · Customer preferences** | Where-to-play matrix (segment CAGR vs Ford units sold, bubble = segment size), CAGR by segment for the selected period, segment CAGR heatmap across the cycle (Pre-COVID 2015–19, COVID + chips 2019–22, Recovery 2022–25, Decade 2015–25), growth index and CAGR for emerging segments (minivans, hybrids, PHEV, BEV), electrified sales and penetration |
| **Recommendations** | 3 moves, each with a backing chart: build more (and more models) in Mexico to price against Chinese brands, extend Territory with EV and hybrid options, and a new minivan and sport car |

**Global controls (sidebar):** quick-range presets (Pre-COVID, COVID + chips, Recovery…), an analysis-period slider that drives every chart and CAGR, and a toggle that shades COVID-19 (Mar–Dec 2020) and the chip shortage (2021 to mid-2023). The segment CAGR heatmap uses fixed windows, so it doesn't follow the slider.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

`python -m streamlit` works even when Python's Scripts folder isn't on PATH (the usual cause of "streamlit is not recognized" on Windows).

Run it from the repository root so Streamlit picks up the Ford theme in `.streamlit/config.toml`.

## Data

The app reads `INEGI_Auto_Ventas_Maestro_2015_2025.xlsx` (sheets `Datos` and `Datos_HEV`) which is included at the repository root.

## Deploy on Streamlit Community Cloud

1. On share.streamlit.io, choose **New app** and pick this repo.
2. Set the main file path to `app.py`. Community Cloud installs `requirements.txt` automatically.

## Notes

- Hybrid and EV figures come from INEGI's state-level series, which starts in 2016 and has no brand detail. Ford's hybrid share is computed from model names (Escape HEV, Fusion Híbrido).
- BYD, Tesla and some other brands don't report to INEGI, so EV volumes are understated.
- Segments are kept as INEGI reports them. For example, Ford Expedition is classified as a minivan and Transit as an SUV.
- "Chinese brands (all)" in the head-to-head sums MG Motor, JAC, Chirey, Omoda, Jetour, Jetour Soueast, Changan, Geely, Great Wall Motor, GAC, Foton, Motornation (Changan, BAIC and JMC models) and Auteco. Volvo and Smart have Chinese owners but are left out as European brands. Most Chinese brands started selling after 2015, so their CAGR from 2015 shows as —.
- The Ford logo (`ford_logo.svg`, from Wikimedia Commons) is a trademark of Ford Motor Company and is used here only to identify the subject of the analysis. This is an independent academic project, not affiliated with or endorsed by Ford. The header colours are taken from the logo's blues.
- The segment colours were checked for colour-blind separation. Every chart also has a legend or direct labels, and the first three tabs each have a data table.
