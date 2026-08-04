"""Core analysis pipeline for Platskollen.

Unlike platskollen.sources, these modules contain real, runnable logic —
terrain math, exclusion-overlay geometry, and scoring — that requires no
external API access. They operate on whatever GeoDataFrames/rasters are
handed to them, whether that's real Lantmäteriet/Länsstyrelsen data (once
platskollen.sources is wired up) or the synthetic fixtures used by
``platskollen screen --mock`` and the test suite.
"""
