"""Länsstyrelsen (County Administrative Boards) statutory exclusion-layer
fetchers, served via Geodatakatalogen
(https://ext-geodatakatalog.lansstyrelsen.se/).

Covers the administrative/statutory exclusion zones Platskollen screens
against: Natura 2000 (SCI/SPA), riksintresse (naturvård, friluftsliv,
vindbruk), and strandskydd. These are WFS services; some require a
registered API key (see platskollen.config.ENV_LANSSTYRELSEN_API_KEY), others
are anonymous-access open data — the specific auth requirement varies per
layer and is resolved at wiring time, not guessed here.

This module is a Trust Stage 1 skeleton: it raises NotImplementedError
rather than fabricating exclusion polygons. A fabricated "pass" on a hard
exclusion (Natura 2000, riksintresse) is exactly the failure mode the soul
file exists to prevent — so this stub fails loudly instead.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import geopandas as gpd

BBox = tuple[float, float, float, float]  # (minx, miny, maxx, maxy) in EPSG:3006

# Exclusion layer keys returned by fetch_exclusion_layers. These match
# platskollen.config.HARD_EXCLUSION_CATEGORIES plus strandskydd, which is a
# statutory (but not "hard" in the backtest sense) exclusion.
EXCLUSION_LAYER_KEYS = (
    "natura2000",
    "riksintresse_naturvard",
    "riksintresse_friluftsliv",
    "riksintresse_vindbruk",
    "strandskydd",
)


def fetch_exclusion_layers(bbox: BBox) -> "dict[str, gpd.GeoDataFrame]":
    """Fetch statutory exclusion-zone layers intersecting ``bbox`` from
    Länsstyrelsen's Geodatakatalogen WFS services.

    Target services (each a separate WFS layer in Geodatakatalogen):
      - Natura 2000 (SCI/SPA boundaries, per EU habitats/birds directives).
      - Riksintresse naturvård (nature conservation national interest,
        Miljöbalken 3 kap.).
      - Riksintresse friluftsliv (outdoor recreation national interest,
        Miljöbalken 3 kap.).
      - Riksintresse vindbruk (wind power national interest areas,
        published jointly with Energimyndigheten).
      - Strandskydd (shoreline protection zones, Miljöbalken 7 kap.).

    Each returned GeoDataFrame must carry enough metadata (at minimum a
    last-updated/fetch date) for pipeline.exclusions.flag_stale to evaluate
    the soul-file 6-month staleness rule.

    Args:
        bbox: Bounding box in SWEREF99 TM (EPSG:3006) as
            (minx, miny, maxx, maxy).

    Returns:
        A dict keyed by EXCLUSION_LAYER_KEYS, each value a GeoDataFrame of
        exclusion polygons in EPSG:3006.

    Raises:
        NotImplementedError: always, until Geodatakatalogen WFS wiring
            exists.
    """
    raise NotImplementedError(
        "wire up Geodatakatalogen WFS client — see identity/identity.md scope"
    )
