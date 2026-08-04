"""Statutory exclusion-zone overlay analysis.

This module is real, runnable geopandas logic — no external API dependency.
It implements the soul-file rule directly: a parcel that only partially
overlaps an exclusion polygon, or that is claimed differently by two
exclusion layers, is never silently resolved to pass/fail. It is marked
AMBIGUOUS_BOUNDARY and left for a human reviewer.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import geopandas as gpd
import pandas as pd

from platskollen.config import (
    DEFAULT_STALENESS_THRESHOLD_DAYS,
    STATUS_AMBIGUOUS_BOUNDARY,
    STATUS_DATA_GAP,
    STATUS_EXCLUDED,
    STATUS_OK,
)


def _union(gdf: gpd.GeoDataFrame):
    """Union all geometries in gdf, using the modern or legacy API depending
    on the installed geopandas/shapely version.
    """
    geom = gdf.geometry
    if hasattr(geom, "union_all"):
        return geom.union_all()
    return geom.unary_union  # pragma: no cover - older geopandas fallback


def classify_exclusions(
    parcels: gpd.GeoDataFrame,
    exclusion_layers: dict[str, gpd.GeoDataFrame],
) -> gpd.GeoDataFrame:
    """Classify each parcel against a set of statutory exclusion layers.

    For every parcel, and for every exclusion layer that spatially
    intersects it, this determines whether the parcel is:
      - fully contained within the exclusion geometry (a clean hard
        exclusion for that layer), or
      - only partially overlapping it (the exclusion/parcel boundary
        crosses the parcel) — which the soul file requires be reported as
        AMBIGUOUS_BOUNDARY rather than guessed at, because the correct
        answer would depend on sub-meter precision the source data can't
        guarantee.

    A parcel touched by more than one exclusion layer with inconsistent
    verdicts (e.g. fully excluded by one layer, only boundary-touched by
    another covering an overlapping category) is exactly the "two source
    datasets disagree" case from the soul file, and is likewise marked
    AMBIGUOUS_BOUNDARY rather than silently picking one layer's answer.

    Parcels with missing/empty geometry are marked DATA_GAP — never
    silently dropped from the result.

    Args:
        parcels: GeoDataFrame of candidate parcels. Any existing index is
            preserved on the returned GeoDataFrame.
        exclusion_layers: Mapping of layer name (e.g. "natura2000",
            "riksintresse_vindbruk") to a GeoDataFrame of exclusion
            polygons. Layers that are None or empty are skipped (treated as
            "no data for this layer in this area", not as "clear").

    Returns:
        A copy of ``parcels`` with three added columns:
          - ``exclusion_status``: one of STATUS_OK, STATUS_EXCLUDED,
            STATUS_AMBIGUOUS_BOUNDARY, STATUS_DATA_GAP.
          - ``excluded_by``: list of layer names that fully contain the
            parcel.
          - ``boundary_ambiguous_layers``: list of layer names whose
            geometry intersects the parcel without fully containing it.
    """
    if not isinstance(parcels, gpd.GeoDataFrame):
        raise TypeError("parcels must be a GeoDataFrame")

    statuses: list[str] = []
    excluded_by_col: list[list[str]] = []
    ambiguous_col: list[list[str]] = []

    # Pre-union each layer once (not per-parcel) for efficiency.
    layer_unions: dict[str, Any] = {}
    for name, layer_gdf in exclusion_layers.items():
        if layer_gdf is None or len(layer_gdf) == 0:
            continue
        layer_unions[name] = _union(layer_gdf)

    for geom in parcels.geometry:
        if geom is None or geom.is_empty:
            statuses.append(STATUS_DATA_GAP)
            excluded_by_col.append([])
            ambiguous_col.append([])
            continue

        fully_excluded_by: list[str] = []
        boundary_touching: list[str] = []

        for name, union_geom in layer_unions.items():
            if not geom.intersects(union_geom):
                continue
            if geom.within(union_geom):
                fully_excluded_by.append(name)
            else:
                # Intersects but is not fully contained: the exclusion
                # boundary crosses this parcel, or a second layer disagrees
                # with a first layer's clean verdict for part of the
                # parcel's area. Either way: boundary-level ambiguity.
                boundary_touching.append(name)

        if boundary_touching:
            # Covers both "boundary crosses this parcel" and "two layers
            # disagree" (fully_excluded_by non-empty at the same time as
            # boundary_touching) — both are reported, neither is dropped.
            statuses.append(STATUS_AMBIGUOUS_BOUNDARY)
        elif fully_excluded_by:
            statuses.append(STATUS_EXCLUDED)
        else:
            statuses.append(STATUS_OK)

        excluded_by_col.append(fully_excluded_by)
        ambiguous_col.append(boundary_touching)

    result = parcels.copy()
    result["exclusion_status"] = statuses
    result["excluded_by"] = excluded_by_col
    result["boundary_ambiguous_layers"] = ambiguous_col
    return result


def flag_stale(
    layer_metadata: dict[str, dict[str, Any]],
    max_age_days: int = DEFAULT_STALENESS_THRESHOLD_DAYS,
    *,
    now: datetime | None = None,
) -> dict[str, bool]:
    """Flag which source layers are stale per the soul-file 6-month rule.

    Args:
        layer_metadata: Mapping of layer name to a metadata dict containing
            at least a ``"fetch_date"`` key with a timezone-aware
            ``datetime`` (the date the layer was last verified-refreshed
            from its source). A ``"dataset_name"`` key is recommended for
            citation purposes but not required by this function.
        max_age_days: Maximum age, in days, before a layer is considered
            stale. Defaults to platskollen.config's 180-day rule.
        now: Reference time for the staleness check. Defaults to the
            current UTC time; overridable for deterministic testing.

    Returns:
        A dict mapping each layer name in ``layer_metadata`` to True if
        stale (age > max_age_days) or False otherwise.

    Raises:
        KeyError: if a layer's metadata dict is missing "fetch_date".
        ValueError: if "fetch_date" is not timezone-aware.
    """
    reference_time = now or datetime.now(timezone.utc)
    stale: dict[str, bool] = {}
    for name, meta in layer_metadata.items():
        if "fetch_date" not in meta:
            raise KeyError(f"layer '{name}' metadata is missing 'fetch_date'")
        fetch_date = meta["fetch_date"]
        if fetch_date.tzinfo is None:
            raise ValueError(
                f"layer '{name}' fetch_date must be timezone-aware "
                "(soul-file staleness rule requires an unambiguous age)"
            )
        age = reference_time - fetch_date
        stale[name] = age > timedelta(days=max_age_days)
    return stale
