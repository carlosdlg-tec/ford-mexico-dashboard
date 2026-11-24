# Ford Mexico · Where to invest next

Streamlit dashboard for a strategy review of Ford in the Mexican light-vehicle market (INEGI RAIAVL retail sales, 2015–2025).

| Tab | What it shows |
|---|---|
| **01 · Ford today** | Units by year, market share, units by car segment (units / % mix), top nameplates, country of manufacture |
| **02 · Industry** | Total market (annual / monthly), CAGR by segment, CAGR heatmap across the COVID / chip-shortage cycle, **1v1 company comparison** (total units + segment units by year) |
| **03 · Customer preferences** | Shift from compact/subcompact to SUVs, share gains, growth index and CAGR for emerging segments (minivans, hybrids, PHEV, BEV), electrified sales and penetration |
| **Recommendations** | Where-to-play matrix plus 3 moves: hybrid minivan, Territory hybrid, sport compact vs GTI and León |

**Global controls (sidebar):** quick-range presets (Pre-COVID, COVID + chips, Recovery…), an analysis-period slider that drives every chart and CAGR, and a toggle that shades COVID-19 (Mar–Dec 2020) and the chip shortage (2021 to mid-2023).

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
- The segment colours were checked for colour-blind separation. Every chart also has a legend or direct labels, and each tab has a data table.
