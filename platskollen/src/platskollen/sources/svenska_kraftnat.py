"""Svenska kraftnät (Swedish national transmission grid operator) open-data
fetcher, served via data.svk.se / Kapacitetskarta
(https://data.svk.se/, https://www.svk.se/utveckling-av-kraftsystemet/kartor-och-geografisk-information/kapacitetskartan/).

CRITICAL SCOPE NOTE — repeated from identity/soul.md, do not remove:
Svenska kraftnät publishes capacity and connection-point data for the
TRANSMISSION grid only (regionally: 220/400 kV level). It says nothing about
regional or local DISTRIBUTION grid capacity, which is operated by ~170
separate nätbolag (grid companies) with no unified open API. Platskollen must
never represent this dataset's output as a connection guarantee, and every
report built from it must state explicitly that distribution-grid capacity
requires a direct nätbolag inquiry before any capital commitment. Violating
this is the specific example the soul file calls out under "What you refuse
to do."

This module is a Trust Stage 1 skeleton: it raises NotImplementedError
rather than returning fabricated capacity figures.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import geopandas as gpd

BBox = tuple[float, float, float, float]  # (minx, miny, maxx, maxy) in EPSG:3006


def fetch_transmission_capacity(bbox: BBox) -> "gpd.GeoDataFrame":
    """Fetch transmission-grid connection points and available capacity
    intersecting ``bbox`` from Svenska kraftnät's open Kapacitetskarta /
    data.svk.se dataset.

    Scope reminder (see module docstring and identity/soul.md): this is
    TRANSMISSION grid data only. It must never be used, in this module or by
    any caller, to imply regional/local distribution grid connection
    capacity is known or guaranteed. Downstream code (pipeline.scoring) must
    surface distribution capacity as a permanent DATA_GAP.

    Args:
        bbox: Bounding box in SWEREF99 TM (EPSG:3006) as
            (minx, miny, maxx, maxy).

    Returns:
        A GeoDataFrame of transmission-grid connection points/lines with
        available-capacity attributes, in EPSG:3006.

    Raises:
        NotImplementedError: always, until data.svk.se API wiring exists.
    """
    raise NotImplementedError(
        "wire up data.svk.se API client — see identity/identity.md scope; "
        "note this dataset is TRANSMISSION grid only, never distribution capacity"
    )
