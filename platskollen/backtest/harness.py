#!/usr/bin/env python3
"""Platskollen Stage 1 backtest harness.

Loads paired (agent-output, manual-reference) GeoJSON files from
backtest/cases/ and backtest/reference/, computes per-parcel classification
agreement, and enforces the Stage 1 exit criteria from backtest/README.md:

    20 backtested sites, >=98% exclusion-classification agreement with
    manual QGIS analysis, zero false negatives on hard exclusions.

The hard-exclusion false-negative check is a HARD FAIL (non-zero exit code),
never averaged into the overall agreement percentage — see backtest/README.md
for why. This is deliberately stdlib-only (json + pathlib) so it can run
without the full geopandas/rasterio dependency stack.

Usage:
    python backtest/harness.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKTEST_DIR = Path(__file__).resolve().parent
CASES_DIR = BACKTEST_DIR / "cases"
REFERENCE_DIR = BACKTEST_DIR / "reference"

# Kept in sync with platskollen.config.HARD_EXCLUSION_CATEGORIES. Duplicated
# here (rather than imported) so this harness has zero dependency on the
# platskollen package being installed — it must be runnable standalone.
HARD_EXCLUSION_CATEGORIES = (
    "natura2000",
    "riksintresse_naturvard",
    "riksintresse_friluftsliv",
    "riksintresse_vindbruk",
)

MIN_SITES_REQUIRED = 20
MIN_AGREEMENT_PCT = 98.0


class BacktestError(Exception):
    """Raised for structural problems (mismatched files, bad data)."""


def _load_geojson(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    features = data.get("features", [])
    parcels = {}
    for feature in features:
        props = feature.get("properties", {})
        key = props.get("fastighetsbeteckning")
        if key is None:
            raise BacktestError(
                f"{path}: feature missing 'fastighetsbeteckning' property"
            )
        parcels[key] = props
    return parcels


def _discover_paired_cases() -> list[tuple[str, Path, Path]]:
    """Return (site_id, case_path, reference_path) tuples for every
    <site-id>.geojson present in both cases/ and reference/. Raises if a
    file exists in one directory but not the matched other.
    """
    case_files = {p.stem: p for p in CASES_DIR.glob("*.geojson")}
    reference_files = {p.stem: p for p in REFERENCE_DIR.glob("*.geojson")}

    case_only = set(case_files) - set(reference_files)
    reference_only = set(reference_files) - set(case_files)
    if case_only:
        raise BacktestError(
            f"case file(s) with no matching reference: {sorted(case_only)}"
        )
    if reference_only:
        raise BacktestError(
            f"reference file(s) with no matching case: {sorted(reference_only)}"
        )

    return sorted(
        (site_id, case_files[site_id], reference_files[site_id])
        for site_id in case_files
    )


def run() -> int:
    if not CASES_DIR.exists() or not REFERENCE_DIR.exists():
        print("[backtest] cases/ or reference/ directory missing — nothing to verify.")
        return 0

    try:
        paired = _discover_paired_cases()
    except BacktestError as exc:
        print(f"[backtest] FAIL — {exc}", file=sys.stderr)
        return 1

    if not paired:
        print("[backtest] 0 cases found, nothing to verify.")
        return 0

    total_parcels = 0
    agreeing_parcels = 0
    hard_exclusion_false_negatives: list[str] = []
    site_errors: list[str] = []

    for site_id, case_path, reference_path in paired:
        try:
            case_parcels = _load_geojson(case_path)
            reference_parcels = _load_geojson(reference_path)
        except (BacktestError, json.JSONDecodeError, OSError) as exc:
            site_errors.append(f"{site_id}: {exc}")
            continue

        case_keys = set(case_parcels)
        reference_keys = set(reference_parcels)
        if case_keys != reference_keys:
            missing_in_case = reference_keys - case_keys
            missing_in_reference = case_keys - reference_keys
            site_errors.append(
                f"{site_id}: parcel set mismatch "
                f"(missing in case: {sorted(missing_in_case)}, "
                f"missing in reference: {sorted(missing_in_reference)})"
            )
            continue

        for parcel_id in case_keys:
            case_props = case_parcels[parcel_id]
            ref_props = reference_parcels[parcel_id]

            total_parcels += 1
            if case_props.get("status") == ref_props.get("status"):
                agreeing_parcels += 1

            # Hard exclusion false negative: reference says this parcel is
            # excluded by a hard-exclusion category, but the agent's output
            # did not mark it EXCLUDED. This check ignores the general
            # status agreement metric entirely and is evaluated on its own.
            ref_excluded_by = set(ref_props.get("excluded_by") or [])
            if ref_excluded_by & set(HARD_EXCLUSION_CATEGORIES):
                if case_props.get("status") != "EXCLUDED":
                    hard_exclusion_false_negatives.append(
                        f"{site_id}/{parcel_id}: reference flags hard exclusion "
                        f"{sorted(ref_excluded_by & set(HARD_EXCLUSION_CATEGORIES))} "
                        f"but agent status was '{case_props.get('status')}'"
                    )

    if site_errors:
        print("[backtest] FAIL — structural errors in backtest data:", file=sys.stderr)
        for err in site_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    n_sites = len(paired)
    agreement_pct = (
        (agreeing_parcels / total_parcels * 100.0) if total_parcels else 0.0
    )

    print(f"[backtest] sites evaluated: {n_sites}")
    print(f"[backtest] parcels evaluated: {total_parcels}")
    print(f"[backtest] status agreement: {agreement_pct:.2f}%")
    print(
        f"[backtest] hard-exclusion false negatives: "
        f"{len(hard_exclusion_false_negatives)}"
    )

    failed = False

    if hard_exclusion_false_negatives:
        failed = True
        print(
            "[backtest] HARD FAIL — zero false negatives on hard exclusions is "
            "non-negotiable (see backtest/README.md, no averaging allowed):",
            file=sys.stderr,
        )
        for msg in hard_exclusion_false_negatives:
            print(f"  - {msg}", file=sys.stderr)

    if n_sites < MIN_SITES_REQUIRED:
        failed = True
        print(
            f"[backtest] FAIL — {n_sites}/{MIN_SITES_REQUIRED} required "
            "backtested sites present.",
            file=sys.stderr,
        )

    if total_parcels and agreement_pct < MIN_AGREEMENT_PCT:
        failed = True
        print(
            f"[backtest] FAIL — status agreement {agreement_pct:.2f}% is below "
            f"the required {MIN_AGREEMENT_PCT}%.",
            file=sys.stderr,
        )

    if failed:
        return 1

    print("[backtest] PASS — Stage 1 exit criteria met.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
