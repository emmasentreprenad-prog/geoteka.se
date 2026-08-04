"""Unit tests for platskollen.pipeline.exclusions.

Uses small synthetic GeoDataFrames — no external data or network access.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import geopandas as gpd
import pytest
from shapely.geometry import Polygon

from platskollen.config import (
    STATUS_AMBIGUOUS_BOUNDARY,
    STATUS_DATA_GAP,
    STATUS_EXCLUDED,
    STATUS_OK,
    TARGET_CRS,
)
from platskollen.pipeline.exclusions import classify_exclusions, flag_stale


def _square(cx: float, cy: float, half: float) -> Polygon:
    return Polygon(
        [
            (cx - half, cy - half),
            (cx + half, cy - half),
            (cx + half, cy + half),
            (cx - half, cy + half),
        ]
    )


def test_parcel_fully_clear_is_ok():
    parcels = gpd.GeoDataFrame(
        [{"id": "clean-1", "geometry": _square(0, 0, 10)}], crs=TARGET_CRS
    )
    exclusion_layers = {
        "natura2000": gpd.GeoDataFrame(
            [{"geometry": _square(1000, 1000, 10)}], crs=TARGET_CRS
        )
    }

    result = classify_exclusions(parcels, exclusion_layers)

    assert result.loc[0, "exclusion_status"] == STATUS_OK
    assert result.loc[0, "excluded_by"] == []
    assert result.loc[0, "boundary_ambiguous_layers"] == []


def test_parcel_fully_inside_exclusion_is_excluded():
    parcels = gpd.GeoDataFrame(
        [{"id": "inside-1", "geometry": _square(0, 0, 5)}], crs=TARGET_CRS
    )
    exclusion_layers = {
        "natura2000": gpd.GeoDataFrame(
            [{"geometry": _square(0, 0, 50)}], crs=TARGET_CRS
        )
    }

    result = classify_exclusions(parcels, exclusion_layers)

    assert result.loc[0, "exclusion_status"] == STATUS_EXCLUDED
    assert result.loc[0, "excluded_by"] == ["natura2000"]
    assert result.loc[0, "boundary_ambiguous_layers"] == []


def test_parcel_straddling_boundary_is_ambiguous():
    # Exclusion polygon covers only the right half of the parcel.
    parcels = gpd.GeoDataFrame(
        [{"id": "straddle-1", "geometry": _square(0, 0, 10)}], crs=TARGET_CRS
    )
    exclusion_layers = {
        "riksintresse_vindbruk": gpd.GeoDataFrame(
            [{"geometry": Polygon([(0, -10), (20, -10), (20, 10), (0, 10)])}],
            crs=TARGET_CRS,
        )
    }

    result = classify_exclusions(parcels, exclusion_layers)

    assert result.loc[0, "exclusion_status"] == STATUS_AMBIGUOUS_BOUNDARY
    assert result.loc[0, "boundary_ambiguous_layers"] == ["riksintresse_vindbruk"]


def test_two_layers_disagreeing_is_ambiguous_not_silently_resolved():
    # One layer fully contains the parcel (clean exclude), a second,
    # differently-drawn layer only partially overlaps it. The soul-file
    # rule requires this be surfaced, not silently resolved to either
    # verdict.
    parcels = gpd.GeoDataFrame(
        [{"id": "conflict-1", "geometry": _square(0, 0, 10)}], crs=TARGET_CRS
    )
    exclusion_layers = {
        "riksintresse_vindbruk": gpd.GeoDataFrame(
            [{"geometry": _square(0, 0, 50)}], crs=TARGET_CRS  # fully contains
        ),
        "riksintresse_naturvard": gpd.GeoDataFrame(
            [{"geometry": Polygon([(0, -10), (20, -10), (20, 10), (0, 10)])}],
            crs=TARGET_CRS,  # only partially overlaps
        ),
    }

    result = classify_exclusions(parcels, exclusion_layers)

    assert result.loc[0, "exclusion_status"] == STATUS_AMBIGUOUS_BOUNDARY
    assert result.loc[0, "excluded_by"] == ["riksintresse_vindbruk"]
    assert result.loc[0, "boundary_ambiguous_layers"] == ["riksintresse_naturvard"]


def test_empty_geometry_is_data_gap_not_dropped():
    parcels = gpd.GeoDataFrame(
        [{"id": "empty-1", "geometry": Polygon()}], crs=TARGET_CRS
    )
    result = classify_exclusions(parcels, {})

    assert len(result) == 1  # never silently dropped
    assert result.loc[0, "exclusion_status"] == STATUS_DATA_GAP


def test_empty_exclusion_layer_does_not_cause_data_gap():
    parcels = gpd.GeoDataFrame(
        [{"id": "clean-2", "geometry": _square(0, 0, 10)}], crs=TARGET_CRS
    )
    exclusion_layers = {"strandskydd": gpd.GeoDataFrame(geometry=[], crs=TARGET_CRS)}

    result = classify_exclusions(parcels, exclusion_layers)

    assert result.loc[0, "exclusion_status"] == STATUS_OK


def test_flag_stale_marks_old_layers():
    now = datetime(2026, 8, 4, tzinfo=timezone.utc)
    metadata = {
        "fresh_layer": {"fetch_date": now - timedelta(days=10)},
        "stale_layer": {"fetch_date": now - timedelta(days=200)},
        "boundary_layer": {"fetch_date": now - timedelta(days=180)},
    }

    result = flag_stale(metadata, max_age_days=180, now=now)

    assert result["fresh_layer"] is False
    assert result["stale_layer"] is True
    assert result["boundary_layer"] is False  # exactly at threshold: not stale


def test_flag_stale_requires_timezone_aware_fetch_date():
    metadata = {"bad_layer": {"fetch_date": datetime(2026, 1, 1)}}  # naive
    with pytest.raises(ValueError):
        flag_stale(metadata)


def test_flag_stale_requires_fetch_date_key():
    metadata = {"bad_layer": {}}
    with pytest.raises(KeyError):
        flag_stale(metadata)
