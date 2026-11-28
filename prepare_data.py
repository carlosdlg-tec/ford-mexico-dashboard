"""
Download, load and clean the INEGI RAIAVL tables used by the Ford dashboard.

Source: INEGI, Registro Administrativo de la Industria Automotriz de Vehiculos Ligeros (RAIAVL), open data.
  - Monthly light-vehicle sales by brand, model, segment and country of origin (2005 onward)
  - Monthly hybrid and electric vehicle sales by state (2016 onward, no brand detail)

Output (read by app.py):
  data/raiavl_venta_2015_2025.csv.gz    one row per year, month, brand, model, segment and country of origin
  data/raiavl_hibrido_2016_2025.csv.gz  one row per year, month and state

Run from this folder:
    python prepare_data.py              # downloads the zips into data/raw/ if they are not there yet
    python prepare_data.py --refresh    # downloads them again (INEGI revises recent months)
"""
import argparse
import sys
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
OUT = HERE / "data"

BASE_URL = "https://www.inegi.org.mx/contenidos/datosprimarios/iavl/datosabiertos/"
SALES_ZIP = "conjunto_de_datos_raiavl_mensual_venta_csv.zip"
HYBRID_ZIP = "conjunto_de_datos_raiavl_mensual_hibrido_csv.zip"

SALES_YEARS = range(2015, 2026)   # full years in the analysis
HYBRID_YEARS = range(2016, 2026)  # the hybrid/EV series starts in 2016


# ─────────────────────────────────────────────────────────────────────────────
# 1. Download
# ─────────────────────────────────────────────────────────────────────────────
def download(name: str, refresh: bool = False) -> Path:
    """Save an INEGI zip into data/raw/ (skipped if it is already there)."""
    path = RAW / name
    if path.exists() and not refresh:
        print(f"Using {path.relative_to(HERE)}")
        return path
    RAW.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {BASE_URL + name} ...")
    req = urllib.request.Request(BASE_URL + name, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    if not data.startswith(b"PK"):  # INEGI answers moved links with an HTML page, not an error code
        sys.exit(f"{name}: the download is not a zip file. Check the link on INEGI's RAIAVL open-data page.")
    path.write_bytes(data)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 2. Load
# ─────────────────────────────────────────────────────────────────────────────
def read_years(zf: zipfile.ZipFile, pattern: str, years: range, dtype: dict) -> pd.DataFrame:
    """Stack the one-file-per-year CSVs inside an INEGI zip (files are UTF-8)."""
    frames = []
    for y in years:
        member = f"conjunto_de_datos/{pattern.format(y)}"
        if member not in zf.namelist():
            sys.exit(f"Missing {member} in the zip; INEGI may have renamed it.")
        frames.append(pd.read_csv(zf.open(member), dtype=dtype))
    return pd.concat(frames, ignore_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Clean
# ─────────────────────────────────────────────────────────────────────────────
def clean_sales(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as zf:
        d = read_years(zf, "raiavl_venta_mensual_tr_cifra_{}.csv", SALES_YEARS, {"ID_MES": str})
        months = pd.read_csv(zf.open("catalogos/tc_mes.csv"), dtype=str)
        countries = pd.read_csv(zf.open("catalogos/tc_pais_origen.csv"))

    raw_units = d["UNI_VEH"].sum()
    # PROD_EST and COBERTURA hold the same text on every row ("RAIAVL ... Venta", "Nacional")
    d = d.drop(columns=["PROD_EST", "COBERTURA"])
    # A few model names carry trailing spaces (e.g. "JT ", "Lyriq SUV ")
    for col in ["MARCA", "MODELO", "TIPO", "SEGMENTO", "ORIGEN", "ESTATUS"]:
        d[col] = d[col].str.strip()
    # Readable month and country names from INEGI's catalogs, plus a real date
    d = d.merge(months.rename(columns={"DESCRIPCION_MES": "MES"}), on="ID_MES", how="left")
    d = d.merge(countries.rename(columns={"DESC_PAIS_ORIGEN": "PAIS_ORIGEN"}), on="ID_PAIS_ORIGEN", how="left")
    d["FECHA"] = pd.to_datetime(dict(year=d["ANIO"], month=d["ID_MES"].astype(int), day=1))
    # Rows with 0 units are model listings with no sales that month; they add nothing to any total.
    # Negative rows are kept: they are INEGI corrections to earlier months (e.g. -405 F-150 in Mar 2016).
    d = d[d["UNI_VEH"] != 0]

    # Checks: nothing lost, nothing unmatched
    assert d["UNI_VEH"].sum() == raw_units, "units changed while cleaning"
    assert d[["MES", "PAIS_ORIGEN"]].notna().all().all(), "a month or country code is missing from INEGI's catalog"
    assert sorted(d["ANIO"].unique()) == list(SALES_YEARS), "a year is missing"

    cols = ["ANIO", "ID_MES", "MES", "FECHA", "MARCA", "MODELO", "TIPO", "SEGMENTO",
            "ORIGEN", "ID_PAIS_ORIGEN", "PAIS_ORIGEN", "UNI_VEH", "ESTATUS"]
    return d[cols].sort_values(["ANIO", "ID_MES", "MARCA", "MODELO"]).reset_index(drop=True)


def clean_hybrid(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as zf:
        h = read_years(zf, "raiavl_hibrido_mensual_tr_cifra_{}.csv", HYBRID_YEARS, {"ID_MES": str, "ID_ENTIDAD": str})
        months = pd.read_csv(zf.open("catalogos/tc_mes.csv"), dtype=str)
        states = pd.read_csv(zf.open("catalogos/tc_entidad_federativa.csv"), dtype=str)

    tech = ["VEH_ELECTR", "VEH_HIBRIDAS_PLUGIN", "VEH_HIBRIDAS"]  # BEV, PHEV, HEV
    raw_units = h[tech].sum().sum()
    h = h.drop(columns=["PROD_EST", "COBERTURA"])
    h = h.merge(months.rename(columns={"DESCRIPCION_MES": "MES"}), on="ID_MES", how="left")
    h = h.merge(states.rename(columns={"DESC_ENTIDAD": "ENTIDAD"}), on="ID_ENTIDAD", how="left")
    h["FECHA"] = pd.to_datetime(dict(year=h["ANIO"], month=h["ID_MES"].astype(int), day=1))
    h["TOTAL_ELECTRIFICADOS"] = h[tech].sum(axis=1)

    assert h["TOTAL_ELECTRIFICADOS"].sum() == raw_units, "units changed while cleaning"
    assert h[["MES", "ENTIDAD"]].notna().all().all(), "a month or state code is missing from INEGI's catalog"
    assert sorted(h["ANIO"].unique()) == list(HYBRID_YEARS), "a year is missing"

    cols = ["ANIO", "ID_MES", "MES", "FECHA", "ID_ENTIDAD", "ENTIDAD", *tech, "TOTAL_ELECTRIFICADOS", "ESTATUS"]
    return h[cols].sort_values(["ANIO", "ID_MES", "ID_ENTIDAD"]).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Save
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refresh", action="store_true", help="download the INEGI zips again")
    args = ap.parse_args()

    sales = clean_sales(download(SALES_ZIP, args.refresh))
    hybrid = clean_hybrid(download(HYBRID_ZIP, args.refresh))

    OUT.mkdir(exist_ok=True)
    sales.to_csv(OUT / "raiavl_venta_2015_2025.csv.gz", index=False)
    hybrid.to_csv(OUT / "raiavl_hibrido_2016_2025.csv.gz", index=False)

    print(f"Sales:  {len(sales):,} rows, {sales['UNI_VEH'].sum():,} units, "
          f"{sales['MARCA'].nunique()} brands, {sales['ANIO'].min()}-{sales['ANIO'].max()}")
    print(f"Hybrid: {len(hybrid):,} rows, {hybrid['TOTAL_ELECTRIFICADOS'].sum():,} electrified units, "
          f"{hybrid['ANIO'].min()}-{hybrid['ANIO'].max()}")
    print(f"Saved to {OUT.relative_to(HERE)}/")


if __name__ == "__main__":
    main()
