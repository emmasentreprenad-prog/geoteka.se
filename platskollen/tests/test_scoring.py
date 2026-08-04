"""Unit tests for platskollen.pipeline.scoring.

Uses small synthetic GeoDataFrames — no external data or network access.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import Polygon

from platskollen.config import (
    STATUS_AMBIGUOUS_BOUNDARY,
    STATUS_DATA_GAP,
    STATUS_EXCLUDED,
    STATUS_OK,
    STATUS_STALE_DATA,
    TARGET_CRS,
)
from platskollen.pipeline.scoring import grid_proximity_score, score_parcel, score_parcels


def test_grid_proximity_score_bands():
    assert grid_proximity_score(500) == 1.0
    assert grid_proximity_score(5_000) == 0.6
    assert grid_proximity_score(20_000) == 0.3
    assert grid_proximity_score(50_000) == 0.0
    assert grid_proximity_score(None) is None


def test_grid_proximity_score_rejects_negative_distance():
    with pytest.raises(ValueError):
        grid_proximity_score(-1)


def test_score_parcel_all_signals_present_is_ok():
    result = score_parcel(
        terrain_suitable_fraction=0.9,
        grid_distance_m=1_000,
        land_cover_suitable_fraction=0.8,
        exclusion_status=STATUS_OK,
    )
    assert result.status == STATUS_OK
    assert 0.0 < result.score <= 1.0
    assert result.confidence == 1.0


def test_score_parcel_excluded_forces_zero_score():
    result = score_parcel(
        terrain_suitable_fraction=0.9,
        grid_distance_m=1_000,
        land_cover_suitable_fraction=0.8,
        exclusion_status=STATUS_EXCLUDED,
    )
    assert result.status == STATUS_EXCLUDED
    assert result.score == 0.0


def test_score_parcel_ambiguous_is_never_silently_resolved_to_ok_or_excluded():
    result = score_parcel(
        terrain_suitable_fraction=0.9,
        grid_distance_m=1_000,
        land_cover_suitable_fraction=0.8,
        exclusion_status=STATUS_AMBIGUOUS_BOUNDARY,
    )
    assert result.status == STATUS_AMBIGUOUS_BOUNDARY
    assert result.status not in (STATUS_OK, STATUS_EXCLUDED)
    assert result.confidence == 0.0


def test_score_parcel_missing_signal_triggers_data_gap_not_silent_drop():
    result = score_parcel(
        terrain_suitable_fraction=0.9,
        grid_distance_m=None,  # missing: e.g. Svenska kraftnät fetch failed
        land_cover_suitable_fraction=0.8,
        exclusion_status=STATUS_OK,
    )
    assert result.status == STATUS_DATA_GAP
    # Still produces a usable score from the signals that ARE available.
    assert result.score > 0.0
    assert result.confidence < 1.0


def test_score_parcel_stale_layers_lowers_confidence_and_flags_status():
    result = score_parcel(
        terrain_suitable_fraction=0.9,
        grid_distance_m=1_000,
        land_cover_suitable_fraction=0.8,
        exclusion_status=STATUS_OK,
        stale_layers=["riksintresse_vindbruk"],
    )
    assert result.status == STATUS_STALE_DATA
    assert result.confidence < 1.0


def test_score_parcels_never_drops_a_row():
    parcels = gpd.GeoDataFrame(
        [
            {
                "fastighetsbeteckning": "A 1:1",
                "geometry": Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                "terrain_suitable_fraction": 0.9,
                "grid_distance_m": 1_000,
                "land_cover_suitable_fraction": 0.8,
                "exclusion_status": STATUS_OK,
            },
            {
                "fastighetsbeteckning": "A 1:2",
                "geometry": Polygon([(2, 0), (3, 0), (3, 1), (2, 1)]),
                "terrain_suitable_fraction": np.nan,  # data gap
                "grid_distance_m": 1_000,
                "land_cover_suitable_fraction": 0.8,
                "exclusion_status": STATUS_OK,
            },
        ],
        crs=TARGET_CRS,
    )

    result = score_parcels(parcels)

    assert len(result) == 2
    statuses = set(result["status"])
    assert STATUS_DATA_GAP in statuses
    # Highest score should be ranked first.
    assert result.iloc[0]["score"] >= result.iloc[1]["score"]
