"""Lantmäteriet (Swedish mapping, cadastral and land registration authority)
data fetchers, served via Geotorget (https://www.geotorget.lantmateriet.se/).

All three products below require an OAuth2 client-credentials grant issued
per API product through Geotorget. Credentials are never hardcoded — they are
read from the environment (see platskollen.config.ENV_LANTMATERIET_CLIENT_ID /
ENV_LANTMATERIET_CLIENT_SECRET) at call time by the (not-yet-implemented)
client wiring.

This module is a Trust Stage 1 skeleton: every function has a real signature
and a real docstring describing the actual product it targets, but the body
raises NotImplementedError. It must never pretend to succeed — a mocked
or fabricated response here would violate the soul-file rule against
presenting guesses as fact.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import geopandas as gpd
    import rasterio

BBox = tuple[float, float, float, float]  # (minx, miny, maxx, maxy) in EPSG:3006


def fetch_elevation(bbox: BBox) -> "rasterio.io.DatasetReader":
    """Fetch a digital elevation model raster for ``bbox`` from Lantmäteriet
    höjddata (grid 1+ / 2+, national elevation model derived from airborne
    LiDAR).

    Target product: "Höjddata, grid 1+" via Geotorget's Nedladdning
    (download) API, or the corresponding WCS/OGC API - Coverages service for
    programmatic tile retrieval. Resolution and product tier depend on
    subscription; grid 1+ (1m) is the standard input for slope/aspect work
    in pipeline.terrain.

    Args:
        bbox: Bounding box in SWEREF99 TM (EPSG:3006) as
            (minx, miny, maxx, maxy).

    Returns:
        An open rasterio dataset for the DEM covering ``bbox``.

    Raises:
        NotImplementedError: always, until Geotorget OAuth2 wiring exists.
    """
    raise NotImplementedError(
        "wire up Geotorget OAuth2 client — see identity/identity.md scope"
    )


def fetch_fastighetsindelning(bbox: BBox) -> "gpd.GeoDataFrame":
    """Fetch cadastral parcel boundaries for ``bbox`` from Lantmäteriet
    Fastighetsindelning Nedladdning (property subdivision download product).

    Target product: "Fastighetsindelning: Nedladdning, vektor" via
    Geotorget, delivered as GML application-schema data. Each feature carries
    the official fastighetsbeteckning (property designation) required for
    citation traceability in pipeline.report.

    Args:
        bbox: Bounding box in SWEREF99 TM (EPSG:3006) as
            (minx, miny, maxx, maxy).

    Returns:
        A GeoDataFrame of parcel polygons with at least a
        ``fastighetsbeteckning`` column, in EPSG:3006.

    Raises:
        NotImplementedError: always, until Geotorget OAuth2 wiring exists.
    """
    raise NotImplementedError(
        "wire up Geotorget OAuth2 client — see identity/identity.md scope"
    )


def fetch_marktackedata(bbox: BBox) -> "gpd.GeoDataFrame":
    """Fetch land-cover polygons for ``bbox`` from Lantmäteriet Marktäckedata
    (national land-cover dataset, Sentinel-2 + ancillary-data derived).

    Target product: "Marktäckedata, Nedladdning, vektor" via Geotorget.
    Used for coarse suitability screening (e.g. excluding water, dense
    forest, or built-up land cover before terrain/exclusion analysis).

    Args:
        bbox: Bounding box in SWEREF99 TM (EPSG:3006) as
            (minx, miny, maxx, maxy).

    Returns:
        A GeoDataFrame of land-cover polygons with a land-cover class
        column, in EPSG:3006.

    Raises:
        NotImplementedError: always, until Geotorget OAuth2 wiring exists.
    """
    raise NotImplementedError(
        "wire up Geotorget OAuth2 client — see identity/identity.md scope"
    )
