# Platskollen Backtest — Trust Stage 1

## Stage 1 exit criteria (verbatim, from the deployment plan)

> 20 backtested sites, ≥98% exclusion-classification agreement with manual
> QGIS analysis, zero false negatives on hard exclusions.

Two rules apply here, and neither is negotiable:

1. **≥98% agreement** is computed across *all* backtested parcels, over
   *all* classification categories (`OK`, `EXCLUDED`, `AMBIGUOUS_BOUNDARY`,
   `STALE_DATA`, `DATA_GAP`) — not just hard exclusions.
2. **Zero false negatives on hard exclusions** (Natura 2000, riksintresse —
   see `platskollen.config.HARD_EXCLUSION_CATEGORIES`) is a *separate, hard
   gate*, not folded into the 98% average. A single parcel that the agent
   scored as non-excluded but a manual QGIS reviewer found genuinely inside
   a Natura 2000 or riksintresse boundary fails Stage 1 outright, no matter
   how high the overall agreement percentage is. This is deliberate: this is
   exactly the error category identity/user.md calls out as the one that
   "destroys trust immediately," and identity/soul.md's failure-mode
   statement exists specifically to prevent it. No averaging is allowed to
   paper over it.

Until both conditions are met on 20 real backtested sites, Platskollen stays
in Stage 1 (sandbox/backtest only) — no client-facing use, per the
deployment plan.

## Directory layout

```
backtest/
  cases/       agent-produced GeoJSON output, one file per backtested site
  reference/   the corresponding manual-QGIS-analysis GeoJSON, same filename
```

`harness.py` pairs files by filename between the two directories. A case
without a matching reference (or vice versa) is reported as an error, not
silently skipped.

Both `cases/` and `reference/` are currently empty placeholders
(`.gitkeep`) — no real backtest cases exist yet. Producing them requires an
analyst to run the agent against a real site AND independently perform the
equivalent manual QGIS overlay analysis, which is out of scope for this
scaffold. Populating this directory with 20 real, honest paired cases is the
actual Stage 1 gate; this harness only automates *checking* that gate once
the data exists.

## Adding a new backtest case

1. Run Platskollen against the candidate site and save its GeoJSON output as
   `backtest/cases/<site-id>.geojson`.
2. Independently produce the equivalent manual QGIS exclusion/suitability
   analysis for the same site, as a GeoJSON with matching per-parcel
   properties, saved as `backtest/reference/<site-id>.geojson`.
3. Both files must use the same feature ordering/identifiers
   (`fastighetsbeteckning`) so the harness can match parcels 1:1 across the
   two files.
4. Run `python backtest/harness.py` and confirm it passes (exit code 0).

## Expected feature properties

Each feature in both `cases/*.geojson` and `reference/*.geojson` must carry
at least:

- `fastighetsbeteckning` — used to match parcels between agent output and
  reference.
- `status` — one of `OK`, `EXCLUDED`, `AMBIGUOUS_BOUNDARY`, `STALE_DATA`,
  `DATA_GAP` (agent output), or the manual analyst's equivalent
  classification (reference).
- `excluded_by` (optional but recommended) — list of hard-exclusion category
  names (see `platskollen.config.HARD_EXCLUSION_CATEGORIES`) that
  contributed to an `EXCLUDED` verdict, used to identify hard-exclusion false
  negatives specifically.

## Running the harness

```
python backtest/harness.py
```

With no cases present, it reports "0 cases found, nothing to verify" and
exits 0 — an empty backtest set is not a failure, it's an unstarted Stage 1.
Once cases exist, it exits non-zero (hard fail) on either exit criterion
being unmet, per the "no averaging allowed" rule above.
