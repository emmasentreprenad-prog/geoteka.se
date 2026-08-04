"""Command-line entry point for Platskollen.

Trust Stage 1: the real source fetchers (platskollen.sources.*) are stubs
pending Geotorget/Geodatakatalogen/data.svk.se credentials, so this CLI's
only fully-runnable mode today is ``--mock``, which exercises the entire
terrain -> exclusions -> scoring -> report pipeline against small synthetic
in-memory fixtures. This is deliberate: it proves the pipeline logic itself
is correct and demonstrable, zero-cost and zero external calls, while being
explicit that it is not yet pulling real Swedish geodata.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone

import numpy as np

try:
    import geopandas as gpd
    from shapely.geometry import Polygon
except ImportError:  # pragma: no cover
    print(
        "platskollen requires geopandas/shapely — pip install -r requirements.txt",
        file=sys.stderr,
    )
    raise

from platskollen.config import TARGET_CRS, DEFAULT_SLOPE_THRESHOLD_DEG_SOLAR
from platskollen.pipeline import exclusions, report, scoring, terrain


def _build_mock_parcels() -> "gpd.GeoDataFrame":
    """A handful of synthetic candidate parcels near a fake town center,
    in SWEREF99 TM coordinates roughly plausible for southern Sweden.
    """
    base_x, base_y = 400_000.0, 6_400_000.0

    def square(cx: float, cy: float, half: float = 100.0) -> Polygon:
        return Polygon(
            [
                (cx - half, cy - half),
                (cx + half, cy - half),
                (cx + half, cy + half),
                (cx - half, cy + half),
            ]
        )

    records = [
        # Clean, unobstructed parcel -> should score well, status OK.
        {"fastighetsbeteckning": "Mockby 1:1", "geometry": square(base_x, base_y)},
        # Sits fully inside the mock Natura 2000 polygon -> EXCLUDED.
        {"fastighetsbeteckning": "Mockby 1:2", "geometry": square(base_x + 500, base_y)},
        # Straddles the mock riksintresse boundary -> AMBIGUOUS_BOUNDARY.
        {"fastighetsbeteckning": "Mockby 1:3", "geometry": square(base_x + 1000, base_y)},
        # No grid-distance data available for this one -> DATA_GAP.
        {"fastighetsbeteckning": "Mockby 1:4", "geometry": square(base_x + 1500, base_y)},
    ]
    return gpd.GeoDataFrame(records, geometry="geometry", crs=TARGET_CRS)


def _build_mock_exclusion_layers(parcels: "gpd.GeoDataFrame") -> dict[str, "gpd.GeoDataFrame"]:
    """Synthetic exclusion polygons designed to exercise every status."""
    base_x, base_y = 400_000.0, 6_400_000.0

    natura2000 = gpd.GeoDataFrame(
        [{"name": "Mock Natura 2000 area", "geometry": Polygon(
            [
                (base_x + 300, base_y - 300),
                (base_x + 800, base_y - 300),
                (base_x + 800, base_y + 300),
                (base_x + 300, base_y + 300),
            ]
        )}],
        geometry="geometry",
        crs=TARGET_CRS,
    )

    # Drawn so it only partially covers Mockby 1:3 (straddles its boundary),
    # producing an AMBIGUOUS_BOUNDARY verdict rather than a clean pass/fail.
    riksintresse_vindbruk = gpd.GeoDataFrame(
        [{"name": "Mock riksintresse vindbruk", "geometry": Polygon(
            [
                (base_x + 950, base_y - 300),
                (base_x + 1050, base_y - 300),
                (base_x + 1050, base_y + 300),
                (base_x + 950, base_y + 300),
            ]
        )}],
        geometry="geometry",
        crs=TARGET_CRS,
    )

    return {
        "natura2000": natura2000,
        "riksintresse_vindbruk": riksintresse_vindbruk,
        # strandskydd deliberately empty here -> no effect, not a data gap
        # (an empty/missing layer means "nothing found in this area", which
        # is different from "this layer could not be checked at all").
        "strandskydd": gpd.GeoDataFrame(geometry=[], crs=TARGET_CRS),
    }


def _mock_terrain_fraction(fastighetsbeteckning: str) -> float:
    """Synthetic terrain suitability, computed via the REAL terrain module
    against a small synthetic DEM, so this exercises actual slope math
    rather than hardcoding a suitability number.
    """
    rng = np.random.default_rng(abs(hash(fastighetsbeteckning)) % (2**32))
    dem = rng.normal(loc=50.0, scale=2.0, size=(20, 20))
    result = terrain.compute_slope_aspect(dem, cell_size=1.0)
    return terrain.mean_slope_fraction_suitable(
        result.slope_deg, DEFAULT_SLOPE_THRESHOLD_DEG_SOLAR
    )


def run_mock_pipeline() -> dict:
    """Run the full terrain -> exclusions -> scoring -> report pipeline
    against synthetic fixtures and return the GeoJSON FeatureCollection.
    """
    parcels = _build_mock_parcels()
    exclusion_layers = _build_mock_exclusion_layers(parcels)

    classified = exclusions.classify_exclusions(parcels, exclusion_layers)

    classified["terrain_suitable_fraction"] = classified["fastighetsbeteckning"].apply(
        _mock_terrain_fraction
    )
    classified["land_cover_suitable_fraction"] = 0.85

    # Mockby 1:4 intentionally has no grid-distance signal -> DATA_GAP.
    grid_distances = {
        "Mockby 1:1": 1_500.0,
        "Mockby 1:2": 3_000.0,
        "Mockby 1:3": 8_000.0,
        "Mockby 1:4": None,
    }
    classified["grid_distance_m"] = classified["fastighetsbeteckning"].map(grid_distances)

    scored = scoring.score_parcels(classified)

    sources = [
        report.SourceCitation(
            dataset_name="MOCK Lantmäteriet höjddata (synthetic, --mock only)",
            fetch_date=date.today(),
        ),
        report.SourceCitation(
            dataset_name="MOCK Länsstyrelsen Geodatakatalogen exclusion layers (synthetic, --mock only)",
            fetch_date=date.today(),
        ),
        report.SourceCitation(
            dataset_name="MOCK Svenska kraftnät transmission grid (synthetic, --mock only)",
            fetch_date=date.today(),
        ),
    ]

    return report.build_geojson_report(scored, sources=sources)


def _run_live(bbox: str, project_type: str, out: str) -> int:
    print(
        "Live mode is not available in Trust Stage 1: platskollen.sources.* "
        "fetchers require Geotorget/Geodatakatalogen/data.svk.se OAuth2 "
        "credentials that are not yet wired up (see identity/identity.md). "
        "Use --mock to run the full pipeline against synthetic data, or see "
        "platskollen/README.md for what's stubbed vs real.",
        file=sys.stderr,
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="platskollen",
        description="Sweden-only pre-feasibility site-suitability screening (Trust Stage 1).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    screen = subparsers.add_parser(
        "screen", help="Screen candidate parcels in a bounding box."
    )
    screen.add_argument(
        "--bbox",
        default=None,
        help='Bounding box "minx,miny,maxx,maxy" in EPSG:4326 (WGS84 lat/lon).',
    )
    screen.add_argument(
        "--project-type",
        choices=["solar", "wind"],
        default="solar",
        help="Project type being screened for.",
    )
    screen.add_argument(
        "--out",
        default="report.geojson",
        help="Output GeoJSON path.",
    )
    screen.add_argument(
        "--mock",
        action="store_true",
        help=(
            "Run the full pipeline against small synthetic in-memory data "
            "instead of live Lantmäteriet/Länsstyrelsen/Svenska kraftnät "
            "sources (which are not yet wired up in Trust Stage 1)."
        ),
    )

    args = parser.parse_args(argv)

    if args.command == "screen":
        if args.mock:
            feature_collection = run_mock_pipeline()
            with open(args.out, "w", encoding="utf-8") as f:
                import json

                json.dump(feature_collection, f, ensure_ascii=False, indent=2)
            n = len(feature_collection["features"])
            print(f"[platskollen] --mock run complete: {n} parcels -> {args.out}")
            print(
                f"[platskollen] data as of {datetime.now(timezone.utc).date().isoformat()} "
                "(synthetic mock data — verify before submission)"
            )
            return 0

        if not args.bbox:
            print("error: --bbox is required unless --mock is set", file=sys.stderr)
            return 2

        return _run_live(args.bbox, args.project_type, args.out)

    return 1  # pragma: no cover - unreachable, argparse enforces subcommand


if __name__ == "__main__":
    raise SystemExit(main())
