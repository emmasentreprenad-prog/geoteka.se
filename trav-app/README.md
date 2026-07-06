# Hitta travbanan

Vite + React + TypeScript-app som visar Sveriges travbanor på en karta och
vad som finns i närheten (hotell, mat, bensin, köpcentrum). Ingen backend —
statisk site med Leaflet/OpenStreetMap, Overpass API för POI:er och ATG:s
inofficiella racinginfo-API för tävlingskalender.

## Utveckling

```sh
npm install
npm run dev
```

## Bygg

```sh
npm run build
```

Bygger till `../trav` (base path `/trav/`), som checkas in i repot och
serveras statiskt tillsammans med resten av geoteka.se.

## Data

- `src/data/travbanor.json` — travbanor med verifierade koordinater. Lägg
  bara till banor här när koordinaterna är verifierade mot en riktig källa
  (bansajt, Wikidata/Wikipedia, kartleverantör) — gissa aldrig.
- `src/data/sponsors.json` — valfri sponsorkonfiguration, av som standard.
