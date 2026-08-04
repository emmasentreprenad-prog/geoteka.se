# USER CONTEXT — Platskollen

## Who they are
GIS analysts, project developers, or engineering consultants (WSP/Sweco/AFRY-
scale firms and smaller independent solar/wind developers) working on Swedish
renewable energy projects. Technically literate in GIS concepts (they know what
a shapefile, a CRS, and a buffer zone are) but do NOT want to personally chase
down and reconcile five separate government data portals for every candidate site.

## What they already know (don't re-explain)
- Basic siting criteria (slope, grid proximity, exclusion zones) — they know
  WHY these matter, they just don't want to manually build the overlay every time.
- Swedish planning process basics (municipal planning monopoly, riksintresse,
  detaljplan vs. no plan) — do not lecture them on PBL basics.
- GIS file formats (GeoJSON, GPKG, SWEREF99 TM) — deliver in these formats by
  default without asking.

## What they do NOT want to have to know
- Which specific Lantmäteriet/Länsstyrelsen/Svenska kraftnät API endpoint or
  OAuth2 credential scheme serves which layer, or how to parse Lantmäteriet's
  GML application schema.
- How to reconcile conflicting or differently-dated boundary datasets by hand.
- The internal QGIS/PyQGIS processing chain used to produce the answer — they
  want the output and the citation trail, not the pipeline.

## How they interact with the agent
- Submit a municipality name or a bounding box (drawn on a simple map UI or
  pasted as coordinates), plus project type (solar/wind) and rough capacity.
- Receive a ranked report within a stated turnaround window (Stage-dependent,
  see deployment plan) with every exclusion citation traceable to a named,
  dated source layer.
- Expect every claim to be falsifiable — they will occasionally spot-check a
  parcel manually in QGIS, and the agent's job is to never be caught wrong on
  a hard exclusion (Natura 2000, riksintresse) because that is the one error
  category that destroys trust immediately.

## What "success" looks like to this user
Fewer hours in QGIS doing overlay grunt work, more hours on judgment calls
(landowner relationships, project economics, permitting strategy) that
actually require their expertise.
