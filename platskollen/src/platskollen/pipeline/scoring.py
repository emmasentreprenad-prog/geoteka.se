"""Ranked scoring: combine terrain, exclusion, and grid-proximity signals
into a per-parcel suitability score, confidence, and explicit status.

This module is real, runnable logic — no external API dependency. The
weighting scheme lives in platskollen.config.SCORING_WEIGHTS, documented and
importable rather than buried here, per the soul-file rule that scoring
weights must never change silently without a reviewable diff.

Every parcel that goes in comes out — a parcel with missing terrain, grid,
or land-cover data is never silently dropped. It is scored with whatever
signals are available and tagged DATA_GAP, per the soul-file rule against
omitting a data gap silently from the report.
"""

from __future__ import annotations

from dataclasses import dataclass

import geopandas as gpd

from platskollen.config import (
    GRID_PROXIMITY_BANDS_M,
    SCORING_WEIGHTS,
    STATUS_AMBIGUOUS_BOUNDARY,
    STATUS_DATA_GAP,
    STATUS_EXCLUDED,
    STATUS_OK,
    STATUS_STALE_DATA,
)

# Confidence penalties applied when a signal is missing or stale. These are
# deliberately explicit constants (not magic numbers inline) so a reviewer
# can see and change the confidence model in one place.
_CONFIDENCE_PENALTY_PER_MISSING_SIGNAL = 0.3
_CONFIDENCE_PENALTY_PER_STALE_LAYER = 0.15
_MIN_CONFIDENCE = 0.0
_MAX_CONFIDENCE = 1.0


@dataclass(frozen=True)
class ScoreResult:
    """Per-parcel scoring outcome."""

    score: float
    status: str
    confidence: float


def grid_proximity_score(distance_m: float | None) -> float | None:
    """Convert a distance-to-transmission-grid measurement into a [0, 1]
    proximity score using platskollen.config.GRID_PROXIMITY_BANDS_M.

    Args:
        distance_m: Distance in meters from the parcel to the nearest
            transmission-grid connection point/line, or None if this signal
            is unavailable (data gap).

    Returns:
        A score in [0, 1] where 1.0 is closest, or None if distance_m is
        None (propagates the data gap rather than guessing a value).
    """
    if distance_m is None:
        return None
    if distance_m < 0:
        raise ValueError(f"distance_m must be >= 0, got {distance_m}")
    if distance_m <= GRID_PROXIMITY_BANDS_M["close"]:
        return 1.0
    if distance_m <= GRID_PROXIMITY_BANDS_M["moderate"]:
        return 0.6
    if distance_m <= GRID_PROXIMITY_BANDS_M["far"]:
        return 0.3
    return 0.0


def score_parcel(
    *,
    terrain_suitable_fraction: float | None,
    grid_distance_m: float | None,
    land_cover_suitable_fraction: float | None,
    exclusion_status: str,
    stale_layers: list[str] | None = None,
    weights: dict[str, float] = SCORING_WEIGHTS,
) -> ScoreResult:
    """Compute the score, status, and confidence for a single parcel.

    Status precedence (soul-file explicit-flagging philosophy — never
    silently resolved):
      1. AMBIGUOUS_BOUNDARY — exclusion analysis found a boundary-level
         conflict. Score is not meaningful; routed to human review.
      2. EXCLUDED — a hard statutory exclusion cleanly contains the parcel.
         Score is forced to 0.0.
      3. DATA_GAP — one or more required signals (terrain, grid distance,
         land cover) is missing. The parcel is still scored on whatever
         signals ARE available, but flagged so it is never mistaken for a
         complete, confident answer.
      4. STALE_DATA — all signals are present, but at least one exclusion
         source layer used for this parcel is stale (see
         pipeline.exclusions.flag_stale). Score is computed normally but
         confidence is reduced.
      5. OK — all signals present, no exclusion conflict, no staleness.

    Args:
        terrain_suitable_fraction: Fraction (0-1) of the parcel's terrain
            below the slope threshold (pipeline.terrain), or None if the
            DEM was unavailable for this parcel.
        grid_distance_m: Distance in meters to the nearest transmission grid
            connection (platskollen.sources.svenska_kraftnat), or None if
            unavailable. Note this is TRANSMISSION grid only, per
            identity/soul.md — never treat this as distribution capacity.
        land_cover_suitable_fraction: Fraction (0-1) of the parcel with
            suitable land cover, or None if unavailable.
        exclusion_status: The exclusion_status value produced by
            pipeline.exclusions.classify_exclusions for this parcel.
        stale_layers: Names of any exclusion source layers used for this
            parcel that pipeline.exclusions.flag_stale flagged as stale.
            Defaults to none.
        weights: Scoring weights for the three signals; must contain keys
            "terrain", "grid_proximity", "land_cover". Defaults to
            platskollen.config.SCORING_WEIGHTS.

    Returns:
        A ScoreResult with score in [0, 1] (0.0 for EXCLUDED/AMBIGUOUS
        parcels), a status string, and a confidence in [0, 1].
    """
    stale_layers = stale_layers or []

    if exclusion_status == STATUS_AMBIGUOUS_BOUNDARY:
        return ScoreResult(score=0.0, status=STATUS_AMBIGUOUS_BOUNDARY, confidence=0.0)

    if exclusion_status == STATUS_EXCLUDED:
        # Even a clean hard exclusion loses confidence if the layer that
        # produced it is stale — a stale "excluded" verdict is still a
        # verdict a human should double check.
        confidence = _MAX_CONFIDENCE - (
            _CONFIDENCE_PENALTY_PER_STALE_LAYER * len(stale_layers)
        )
        return ScoreResult(
            score=0.0,
            status=STATUS_EXCLUDED,
            confidence=max(_MIN_CONFIDENCE, confidence),
        )

    grid_score = grid_proximity_score(grid_distance_m)

    signals = {
        "terrain": terrain_suitable_fraction,
        "grid_proximity": grid_score,
        "land_cover": land_cover_suitable_fraction,
    }
    missing = [name for name, value in signals.items() if value is None]

    # Weighted score over only the available signals, renormalized so a
    # missing signal doesn't silently drag the score toward zero — the
    # DATA_GAP status is what communicates "this is incomplete," not a
    # deflated score pretending to be complete.
    available_weight = sum(weights[name] for name in signals if signals[name] is not None)
    if available_weight > 0:
        score = sum(
            weights[name] * value
            for name, value in signals.items()
            if value is not None
        ) / available_weight
    else:
        score = 0.0

    confidence = _MAX_CONFIDENCE
    confidence -= _CONFIDENCE_PENALTY_PER_MISSING_SIGNAL * len(missing)
    confidence -= _CONFIDENCE_PENALTY_PER_STALE_LAYER * len(stale_layers)
    confidence = max(_MIN_CONFIDENCE, min(_MAX_CONFIDENCE, confidence))

    if missing:
        status = STATUS_DATA_GAP
    elif stale_layers:
        status = STATUS_STALE_DATA
    else:
        status = STATUS_OK

    return ScoreResult(score=score, status=status, confidence=confidence)


def score_parcels(
    parcels: gpd.GeoDataFrame,
    *,
    terrain_col: str = "terrain_suitable_fraction",
    grid_distance_col: str = "grid_distance_m",
    land_cover_col: str = "land_cover_suitable_fraction",
    exclusion_status_col: str = "exclusion_status",
    stale_layers_col: str = "stale_layers",
    weights: dict[str, float] = SCORING_WEIGHTS,
) -> gpd.GeoDataFrame:
    """Score every parcel in a GeoDataFrame and rank the result.

    Args:
        parcels: GeoDataFrame with (at minimum) the columns named by the
            *_col arguments. Typically the output of
            pipeline.exclusions.classify_exclusions with terrain/grid/land
            cover columns joined on afterward.
        terrain_col: Column holding terrain_suitable_fraction (float or
            None/NaN for a data gap).
        grid_distance_col: Column holding grid_distance_m (float or
            None/NaN for a data gap).
        land_cover_col: Column holding land_cover_suitable_fraction (float
            or None/NaN for a data gap).
        exclusion_status_col: Column holding the exclusion_status string
            from pipeline.exclusions.classify_exclusions.
        stale_layers_col: Column holding a list of stale layer names per
            parcel (may be missing/absent -> treated as no staleness).
        weights: Scoring weights, see score_parcel.

    Returns:
        A copy of ``parcels`` with added ``score``, ``status``, and
        ``confidence`` columns, sorted by score descending (ties broken by
        confidence descending). No row is ever dropped, including rows with
        status DATA_GAP.
    """
    if not isinstance(parcels, gpd.GeoDataFrame):
        raise TypeError("parcels must be a GeoDataFrame")

    has_stale_col = stale_layers_col in parcels.columns

    scores: list[float] = []
    statuses: list[str] = []
    confidences: list[float] = []

    for _, row in parcels.iterrows():
        terrain_val = row.get(terrain_col)
        grid_val = row.get(grid_distance_col)
        land_cover_val = row.get(land_cover_col)
        exclusion_status = row.get(exclusion_status_col, STATUS_OK)
        stale_layers = row.get(stale_layers_col) if has_stale_col else None

        # pandas represents a missing float as NaN, not None — normalize.
        terrain_val = None if _is_missing(terrain_val) else float(terrain_val)
        grid_val = None if _is_missing(grid_val) else float(grid_val)
        land_cover_val = None if _is_missing(land_cover_val) else float(land_cover_val)
        stale_layers = list(stale_layers) if stale_layers else []

        result = score_parcel(
            terrain_suitable_fraction=terrain_val,
            grid_distance_m=grid_val,
            land_cover_suitable_fraction=land_cover_val,
            exclusion_status=exclusion_status,
            stale_layers=stale_layers,
            weights=weights,
        )
        scores.append(result.score)
        statuses.append(result.status)
        confidences.append(result.confidence)

    result_gdf = parcels.copy()
    result_gdf["score"] = scores
    result_gdf["status"] = statuses
    result_gdf["confidence"] = confidences
    return result_gdf.sort_values(
        by=["score", "confidence"], ascending=[False, False]
    )


def _is_missing(value) -> bool:
    """True if value should be treated as a data gap (None or NaN)."""
    if value is None:
        return True
    try:
        return bool(value != value)  # NaN != NaN
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return False
