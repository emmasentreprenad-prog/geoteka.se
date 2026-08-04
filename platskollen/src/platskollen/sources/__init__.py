"""Source-data fetchers for Platskollen.

Every module in this package talks to a real Swedish government open-data
service. As of Trust Stage 1 (sandbox/backtest), none of these are wired to
live credentials — each function is a real, documented signature that raises
NotImplementedError rather than silently returning fake data. See
platskollen/README.md, "what's stubbed vs real".
"""
