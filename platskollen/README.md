# Platskollen

Sweden-only pre-feasibility site-suitability screening agent for solar and
onshore wind development. **Trust Stage 1: sandbox/backtest only — no
client-facing use yet.** See `identity/soul.md`, `identity/identity.md`, and
`identity/user.md` for the full operational contract this code must honor,
and `backtest/README.md` for the Stage 1 exit criteria.

## Definition of Done (verbatim, from the business blueprint)

> For any developer-submitted municipality or bounding box in Sweden, the
> agent delivers a ranked, cited GeoJSON + PDF report of candidate
> solar/wind parcels — each scored on slope, aspect, grid proximity, and
> statutory exclusion-zone status (Natura 2000, riksintresse, strandskydd,
> existing vindbruksplan boundaries), tagged with fastighetsbeteckning —
> within 24 hours of request, with zero manual GIS overlay work performed by
> the client.

This scaffold is a step toward that DoD, not the DoD itself. It is not yet
client-facing (Trust Stage 1: sandbox/backtest, per the deployment plan) — see
"What's stubbed vs real" below.

## Install

```bash
cd platskollen
pip install -r requirements.txt
pip install -e .          # registers the `platskollen` package (src layout)
```

`geopandas`/`rasterio`/`pyogrio` pull in compiled geospatial libraries (GDAL,
GEOS, PROJ). If a full install isn't feasible in a given environment, at
minimum `pytest tests/` exercises the pure-Python scoring/exclusion logic —
see the honesty table below for what does and doesn't need the full stack.

## Run the mock pipeline end-to-end

The three real Swedish data-source fetchers
(`src/platskollen/sources/*.py`) are honest `NotImplementedError` stubs
pending Geotorget/Geodatakatalogen/data.svk.se OAuth2 credentials (see
`identity/identity.md`). Everything downstream of them — terrain math,
exclusion-zone overlay, scoring, and GeoJSON report generation — is real,
runnable code with zero external dependency. `--mock` exercises that full
chain against small synthetic in-memory fixtures, so the pipeline is
demonstrably runnable today, at zero cost, with zero external calls:

```bash
python -m platskollen.cli screen --mock --out report.geojson
```

This produces a ranked GeoJSON with one feature per synthetic parcel,
including a status of `OK`, `EXCLUDED`, `AMBIGUOUS_BOUNDARY`, or `DATA_GAP`
depending on which synthetic exclusion/data-availability scenario each mock
parcel was built to exercise (see `_build_mock_parcels` in `src/platskollen/cli.py`).

Live mode (`--bbox` without `--mock`) is intentionally not runnable yet — it
prints a clear message pointing at this README instead of pretending to
fetch real data.

## Run the backtest harness

```bash
python backtest/harness.py
```

With no real backtest cases yet present (`backtest/cases/` and
`backtest/reference/` are empty placeholders), this reports
`0 cases found, nothing to verify` and exits 0. Once real paired
agent-output/manual-QGIS-reference cases are added (see
`backtest/README.md`), it enforces the Stage 1 exit criteria — 20 sites,
≥98% classification agreement, and a hard, non-averaged zero-tolerance check
on hard-exclusion false negatives.

## Run the tests

```bash
pytest tests/
```

Covers `pipeline/scoring.py` and `pipeline/exclusions.py` against small
synthetic GeoDataFrames, specifically verifying the `AMBIGUOUS_BOUNDARY` and
`DATA_GAP` status logic — the two statuses that directly implement the
soul-file rule against silently resolving uncertainty.

## What's stubbed vs real

| Component | Status | Notes |
|---|---|---|
| `pipeline/terrain.py` (slope/aspect from DEM) | **Real** | Pure numpy, Horn's method; no external API. |
| `pipeline/exclusions.py` (overlay + ambiguity + staleness) | **Real** | Real geopandas geometry logic. |
| `pipeline/scoring.py` (weighted ranked score + confidence + status) | **Real** | Documented weights in `config.py`, not hidden. |
| `pipeline/report.py` — GeoJSON export | **Real** | Full citation trail (`sources` per feature) implemented. |
| `pipeline/report.py` — PDF export | **Stub** | `NotImplementedError`; candidates: `reportlab` or `weasyprint`. |
| `sources/lantmateriet.py` | **Stub** | `NotImplementedError`; needs Geotorget OAuth2 (höjddata, Fastighetsindelning, Marktäckedata). |
| `sources/lansstyrelsen.py` | **Stub** | `NotImplementedError`; needs Geodatakatalogen WFS access (Natura 2000, riksintresse, strandskydd). |
| `sources/svenska_kraftnat.py` | **Stub** | `NotImplementedError`; needs data.svk.se access (transmission grid only — see soul-file constraint repeated in the module docstring). |
| CLI `--mock` mode | **Real** | Runs the entire real pipeline end-to-end on synthetic fixtures. |
| CLI live mode | **Not runnable** | Prints an explicit message; does not pretend to fetch real data. |

## Trust stage

This is **Trust Stage 1**: sandbox/backtest only, per the deployment plan.
It is not deployed for client use, and none of the live source integrations
are wired to credentials. Progression past Stage 1 requires the backtest
criteria in `backtest/README.md` to be met on 20 real sites — that data does
not exist yet and is out of scope for this scaffold.
