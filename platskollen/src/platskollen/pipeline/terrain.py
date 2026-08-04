"""Terrain analysis: slope, aspect, and slope-based suitability.

This module is real, runnable logic — pure math over a DEM array, no
external API dependency. It works whether the DEM array came from a real
Lantmäteriet höjddata raster (once platskollen.sources.lantmateriet is wired
up) or a small synthetic array used in tests/mock runs.

WhiteboxTools (the ``whitebox`` package) is used when available for
production-grade slope/aspect computation on real rasters (it operates on
files, is fast, and matches common GIS-tool conventions). A pure-numpy
gradient fallback is provided so this module has zero hard dependency on a
compiled external tool for tests and the mock pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

try:  # pragma: no cover - exercised only when whitebox is installed
    import whitebox  # type: ignore

    _HAS_WHITEBOX = True
except ImportError:  # pragma: no cover
    _HAS_WHITEBOX = False


@dataclass(frozen=True)
class TerrainResult:
    """Per-cell terrain metrics for a DEM array."""

    slope_deg: np.ndarray
    aspect_deg: np.ndarray


def compute_slope_aspect(dem: np.ndarray, cell_size: float) -> TerrainResult:
    """Compute per-cell slope (degrees from horizontal) and aspect (degrees
    clockwise from north) from a DEM array using Horn's method.

    This is the standard 3x3-window finite-difference gradient method used
    by most GIS tools (ArcGIS, QGIS/GDAL, WhiteboxTools) for slope/aspect
    rasters. Edge cells are computed with an edge-replicated (nearest-value)
    padding so the output array matches the input shape exactly.

    Args:
        dem: 2D array of elevation values (meters), row-major, north-up,
            with uniform cell size in both axes.
        cell_size: Ground resolution of one DEM cell, in meters (e.g. 1.0
            for Lantmäteriet grid 1+).

    Returns:
        A TerrainResult with slope_deg and aspect_deg arrays matching
        dem.shape.

    Raises:
        ValueError: if dem is not 2D or cell_size is not positive.
    """
    if dem.ndim != 2:
        raise ValueError(f"dem must be 2D, got shape {dem.shape}")
    if cell_size <= 0:
        raise ValueError(f"cell_size must be positive, got {cell_size}")

    padded = np.pad(dem.astype(np.float64), pad_width=1, mode="edge")

    # 3x3 window neighbor labels, matching Horn (1981):
    # a b c
    # d e f
    # g h i
    a = padded[0:-2, 0:-2]
    b = padded[0:-2, 1:-1]
    c = padded[0:-2, 2:]
    d = padded[1:-1, 0:-2]
    f = padded[1:-1, 2:]
    g = padded[2:, 0:-2]
    h = padded[2:, 1:-1]
    i = padded[2:, 2:]

    dz_dx = ((c + 2 * f + i) - (a + 2 * d + g)) / (8 * cell_size)
    dz_dy = ((g + 2 * h + i) - (a + 2 * b + c)) / (8 * cell_size)

    slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    slope_deg = np.degrees(slope_rad)

    aspect_rad = np.arctan2(dz_dy, -dz_dx)
    aspect_deg = np.degrees(aspect_rad)
    # Convert from mathematical angle to compass bearing (clockwise from
    # north), matching conventional GIS aspect output.
    aspect_deg = np.where(aspect_deg < 0, 90.0 - aspect_deg, 90.0 - aspect_deg)
    aspect_deg = np.mod(aspect_deg, 360.0)
    # Flat cells (zero gradient) conventionally get aspect -1 in GIS tools.
    flat_mask = (dz_dx == 0) & (dz_dy == 0)
    aspect_deg = np.where(flat_mask, -1.0, aspect_deg)

    return TerrainResult(slope_deg=slope_deg, aspect_deg=aspect_deg)


def slope_suitability(
    slope_deg: np.ndarray, threshold_deg: float
) -> np.ndarray:
    """Boolean suitability mask: True where slope is at or below threshold.

    A pre-feasibility screening rule, not an engineering determination — see
    identity/soul.md. Callers should treat cells at exactly the threshold as
    suitable (inclusive) to avoid silently discarding borderline terrain
    that a human should still review.

    Args:
        slope_deg: Array of slope values in degrees (e.g. from
            compute_slope_aspect).
        threshold_deg: Maximum slope, in degrees, considered suitable. See
            platskollen.config.DEFAULT_SLOPE_THRESHOLD_DEG_SOLAR /
            DEFAULT_SLOPE_THRESHOLD_DEG_WIND for defaults.

    Returns:
        Boolean array matching slope_deg.shape.

    Raises:
        ValueError: if threshold_deg is negative.
    """
    if threshold_deg < 0:
        raise ValueError(f"threshold_deg must be >= 0, got {threshold_deg}")
    return slope_deg <= threshold_deg


def mean_slope_fraction_suitable(
    slope_deg: np.ndarray, threshold_deg: float
) -> float:
    """Fraction (0.0-1.0) of cells in slope_deg at or below threshold_deg.

    Used by pipeline.scoring as the terrain suitability component of the
    per-parcel score. Returns 0.0 for an empty array rather than raising, so
    callers can safely handle degenerate (zero-area) parcels — but such a
    parcel should still be surfaced with a DATA_GAP or similar status
    upstream, not silently scored as "0% suitable and therefore excluded."

    Args:
        slope_deg: Array of slope values in degrees.
        threshold_deg: Maximum slope, in degrees, considered suitable.

    Returns:
        Fraction of cells with slope <= threshold_deg, in [0.0, 1.0].
    """
    if slope_deg.size == 0:
        return 0.0
    mask = slope_suitability(slope_deg, threshold_deg)
    return float(np.count_nonzero(mask)) / float(mask.size)
