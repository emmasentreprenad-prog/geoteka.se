"""Central configuration constants for Platskollen.

Keeping these in one place is a direct consequence of the soul-file rule that
scoring weights and thresholds must never change silently: any edit here is a
single, reviewable diff, not logic buried inside a pipeline module.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Coordinate reference system
# ---------------------------------------------------------------------------
# Platskollen operates exclusively in Sweden. Every geometry the pipeline
# produces, accepts, or reasons about must be in SWEREF99 TM. Source data that
# arrives in another CRS (e.g. WGS84 bounding boxes from a UI) must be
# reprojected to this CRS immediately at ingestion, before any spatial
# analysis happens.
TARGET_CRS = "EPSG:3006"  # SWEREF99 TM

# WGS84 is the assumed CRS for user-submitted bounding boxes (lat/lon), which
# the CLI reprojects to TARGET_CRS before anything else runs.
INPUT_BBOX_CRS = "EPSG:4326"

# ---------------------------------------------------------------------------
# Terrain thresholds
# ---------------------------------------------------------------------------
# Default maximum slope (degrees) considered suitable for ground-mount solar.
# This is a screening default, not an engineering spec — see pipeline/terrain.py.
DEFAULT_SLOPE_THRESHOLD_DEG_SOLAR = 10.0

# Default maximum slope (degrees) considered suitable for onshore wind turbine
# foundations at a pre-feasibility level.
DEFAULT_SLOPE_THRESHOLD_DEG_WIND = 15.0

# ---------------------------------------------------------------------------
# Data staleness
# ---------------------------------------------------------------------------
# Soul-file rule: any exclusion-zone dataset not verified-refreshed within this
# many days must be flagged STALE and confidence lowered accordingly.
DEFAULT_STALENESS_THRESHOLD_DAYS = 180

# ---------------------------------------------------------------------------
# Grid proximity
# ---------------------------------------------------------------------------
# Distance bands (meters) used to score proximity to the transmission grid.
# NOTE: transmission grid only — see sources/svenska_kraftnat.py and
# identity/identity.md. Regional/local distribution capacity is a permanent
# DATA_GAP, never estimated.
GRID_PROXIMITY_BANDS_M = {
    "close": 2_000,
    "moderate": 10_000,
    "far": 25_000,
}

# ---------------------------------------------------------------------------
# Scoring weights (documented, not hidden — see pipeline/scoring.py)
# ---------------------------------------------------------------------------
SCORING_WEIGHTS = {
    "terrain": 0.4,
    "grid_proximity": 0.35,
    "land_cover": 0.25,
}

# ---------------------------------------------------------------------------
# Credentials (env var names only — no secrets live in this repo)
# ---------------------------------------------------------------------------
# Lantmäteriet Geotorget uses OAuth2 client-credentials grants per API product.
ENV_LANTMATERIET_CLIENT_ID = "LANTMATERIET_CLIENT_ID"
ENV_LANTMATERIET_CLIENT_SECRET = "LANTMATERIET_CLIENT_SECRET"

# Länsstyrelsen Geodatakatalogen WFS endpoints — most layers are open/anonymous,
# but some require a registered API key.
ENV_LANSSTYRELSEN_API_KEY = "LANSSTYRELSEN_API_KEY"

# Svenska kraftnät data.svk.se — open data; no credential required today, but
# the env var is reserved in case that changes.
ENV_SVENSKA_KRAFTNAT_API_KEY = "SVENSKA_KRAFTNAT_API_KEY"

# ---------------------------------------------------------------------------
# Output status vocabulary (soul-file explicit-flagging philosophy)
# ---------------------------------------------------------------------------
STATUS_OK = "OK"
STATUS_AMBIGUOUS_BOUNDARY = "AMBIGUOUS_BOUNDARY"
STATUS_STALE_DATA = "STALE_DATA"
STATUS_EXCLUDED = "EXCLUDED"
STATUS_DATA_GAP = "DATA_GAP"

ALL_STATUSES = (
    STATUS_OK,
    STATUS_AMBIGUOUS_BOUNDARY,
    STATUS_STALE_DATA,
    STATUS_EXCLUDED,
    STATUS_DATA_GAP,
)

# Exclusion categories considered "hard" — a false negative on any of these is
# a Stage 1 hard-fail per the backtest harness (backtest/README.md).
HARD_EXCLUSION_CATEGORIES = (
    "natura2000",
    "riksintresse_naturvard",
    "riksintresse_friluftsliv",
    "riksintresse_vindbruk",
)
