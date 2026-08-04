"""Report generation: GeoJSON (real, runnable) and PDF (stub).

The GeoJSON output is Platskollen's core deliverable and directly implements
the citation-traceability requirement from identity/identity.md and
identity/soul.md: every feature carries a ``sources`` list naming each
dataset and its fetch date, so a client can verify (and a backtest can
check) exactly what the score was based on.

PDF export is intentionally NOT implemented yet — it's a presentation layer
on top of the same data, not core pipeline logic, and faking it here would
violate the soul-file rule against pretending to succeed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any

import geopandas as gpd

from platskollen.config import TARGET_CRS

REQUIRED_PROPERTY_KEYS = (
    "fastighetsbeteckning",
    "score",
    "status",
    "confidence",
    "sources",
)


@dataclass(frozen=True)
class SourceCitation:
    """One entry in a feature's citation trail."""

    dataset_name: str
    fetch_date: date

    def to_dict(self) -> dict[str, str]:
        return {"dataset_name": self.dataset_name, "fetch_date": self.fetch_date.isoformat()}


def build_geojson_report(
    parcels: gpd.GeoDataFrame,
    *,
    sources: list[SourceCitation],
    fastighetsbeteckning_col: str = "fastighetsbeteckning",
) -> dict[str, Any]:
    """Build the ranked GeoJSON report from scored parcels.

    Args:
        parcels: GeoDataFrame that has already been through
            pipeline.exclusions.classify_exclusions and
            pipeline.scoring.score_parcels — i.e. it must have ``score``,
            ``status``, and ``confidence`` columns, plus a column named by
            ``fastighetsbeteckning_col`` identifying each parcel.
        sources: The full citation trail for this report run — every
            dataset that was consulted (or attempted) to produce it, with
            its fetch date. Applied identically to every feature, since a
            report run queries the same source snapshot for every parcel
            in it. Per identity/soul.md, this list must be honest: if a
            source could not be fetched (e.g. a NotImplementedError stub),
            it should not appear here as if it succeeded.
        fastighetsbeteckning_col: Column holding the property designation.

    Returns:
        A GeoJSON FeatureCollection dict (RFC 7946) in TARGET_CRS
        (EPSG:3006, SWEREF99 TM), where every feature's properties include
        all of REQUIRED_PROPERTY_KEYS.

    Raises:
        ValueError: if a required column is missing from ``parcels``, or if
            ``parcels`` is not in TARGET_CRS.
    """
    required_cols = {fastighetsbeteckning_col, "score", "status", "confidence"}
    missing_cols = {c for c in required_cols if c not in parcels.columns}
    if missing_cols:
        raise ValueError(f"parcels is missing required column(s): {sorted(missing_cols)}")

    if parcels.crs is not None and str(parcels.crs).upper() != TARGET_CRS.upper():
        raise ValueError(
            f"parcels must be in {TARGET_CRS} (SWEREF99 TM), got {parcels.crs}"
        )

    source_dicts = [s.to_dict() for s in sources]

    raw = json.loads(parcels.to_json())
    for feature in raw["features"]:
        props = feature["properties"]
        props["fastighetsbeteckning"] = props.get(fastighetsbeteckning_col)
        props["sources"] = source_dicts
        for key in REQUIRED_PROPERTY_KEYS:
            if key not in props:
                raise ValueError(
                    f"internal error: feature missing required property '{key}'"
                )

    raw.setdefault("crs", {"type": "name", "properties": {"name": f"urn:ogc:def:crs:{TARGET_CRS.replace(':', '::')}"}})
    return raw


def write_geojson_report(
    parcels: gpd.GeoDataFrame,
    out_path: str,
    *,
    sources: list[SourceCitation],
    fastighetsbeteckning_col: str = "fastighetsbeteckning",
) -> str:
    """Build the GeoJSON report and write it to ``out_path``.

    Args:
        parcels: See build_geojson_report.
        out_path: Destination file path.
        sources: See build_geojson_report.
        fastighetsbeteckning_col: See build_geojson_report.

    Returns:
        The path written (same as out_path), for convenient chaining.
    """
    feature_collection = build_geojson_report(
        parcels, sources=sources, fastighetsbeteckning_col=fastighetsbeteckning_col
    )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(feature_collection, f, ensure_ascii=False, indent=2)
    return out_path


def build_pdf_report(parcels: gpd.GeoDataFrame, out_path: str) -> str:
    """Render a client-facing PDF summary of the ranked report.

    Not implemented in Trust Stage 1. A free, self-hostable option to wire
    up later: ``reportlab`` (pure-Python PDF generation) or ``weasyprint``
    (render an HTML/CSS report template to PDF) — either avoids a paid
    rendering service and keeps the pipeline dependency-light.

    Args:
        parcels: Scored GeoDataFrame, same shape as build_geojson_report
            expects.
        out_path: Intended destination file path.

    Raises:
        NotImplementedError: always, in Trust Stage 1.
    """
    raise NotImplementedError(
        "PDF export not yet implemented — wire up reportlab or weasyprint; "
        "see platskollen/README.md 'what's stubbed vs real'"
    )
