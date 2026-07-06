import type { Poi, PoiCategory } from '../types'
import { haversineDistanceM } from '../utils/geo'
import { readCache, writeCache } from '../utils/sessionCache'

const OVERPASS_ENDPOINT = 'https://overpass-api.de/api/interpreter'
const RADIUS_M = 5000
const MAX_RETRIES = 2
const RETRY_DELAY_MS = 1500
const REQUEST_TIMEOUT_MS = 25000

interface OverpassElement {
  type: 'node' | 'way' | 'relation'
  id: number
  lat?: number
  lon?: number
  center?: { lat: number; lon: number }
  tags?: Record<string, string>
}

interface OverpassResponse {
  elements: OverpassElement[]
}

const CATEGORY_TAGS: { category: PoiCategory; key: string; value: string }[] = [
  { category: 'hotel', key: 'tourism', value: 'hotel' },
  { category: 'fast_food', key: 'amenity', value: 'fast_food' },
  { category: 'restaurant', key: 'amenity', value: 'restaurant' },
  { category: 'fuel', key: 'amenity', value: 'fuel' },
  { category: 'supermarket', key: 'shop', value: 'supermarket' },
  { category: 'mall', key: 'shop', value: 'mall' },
]

function buildQuery(lat: number, lng: number): string {
  const clauses = CATEGORY_TAGS.flatMap(({ key, value }) => [
    `node["${key}"="${value}"](around:${RADIUS_M},${lat},${lng});`,
    `way["${key}"="${value}"](around:${RADIUS_M},${lat},${lng});`,
  ]).join('\n  ')
  return `[out:json][timeout:25];\n(\n  ${clauses}\n);\nout center;`
}

function categoryForTags(tags: Record<string, string>): PoiCategory | null {
  const match = CATEGORY_TAGS.find(
    ({ key, value }) => tags[key] === value,
  )
  return match ? match.category : null
}

function elementToPoi(
  el: OverpassElement,
  trackLat: number,
  trackLng: number,
): Poi | null {
  if (!el.tags) return null
  const category = categoryForTags(el.tags)
  if (!category) return null

  const lat = el.type === 'node' ? el.lat : el.center?.lat
  const lng = el.type === 'node' ? el.lon : el.center?.lon
  if (lat === undefined || lng === undefined) return null

  const name = el.tags.name ?? defaultNameForCategory(category)

  return {
    id: `${el.type}/${el.id}`,
    category,
    name,
    lat,
    lng,
    distanceM: haversineDistanceM(trackLat, trackLng, lat, lng),
    address: buildAddress(el.tags),
    sponsored: false,
  }
}

function defaultNameForCategory(category: PoiCategory): string {
  switch (category) {
    case 'hotel':
      return 'Hotell'
    case 'fast_food':
      return 'Snabbmat'
    case 'restaurant':
      return 'Restaurang'
    case 'fuel':
      return 'Bensinstation'
    case 'supermarket':
      return 'Livsmedelsbutik'
    case 'mall':
      return 'Köpcentrum'
  }
}

function buildAddress(tags: Record<string, string>): string | undefined {
  const street = tags['addr:street']
  const number = tags['addr:housenumber']
  const city = tags['addr:city']
  const parts = [street && number ? `${street} ${number}` : street, city].filter(Boolean)
  return parts.length > 0 ? parts.join(', ') : undefined
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export class OverpassError extends Error {}

async function fetchOverpass(query: string): Promise<OverpassResponse> {
  let lastError: unknown

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

    try {
      const response = await fetch(OVERPASS_ENDPOINT, {
        method: 'POST',
        body: `data=${encodeURIComponent(query)}`,
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        signal: controller.signal,
      })
      clearTimeout(timeoutId)

      if (response.status === 429 || response.status === 504) {
        lastError = new OverpassError(
          `Overpass svarade ${response.status} (upptagen). Försöker igen...`,
        )
        await delay(RETRY_DELAY_MS * (attempt + 1))
        continue
      }

      if (!response.ok) {
        throw new OverpassError(`Overpass-fel: ${response.status}`)
      }

      return (await response.json()) as OverpassResponse
    } catch (err) {
      clearTimeout(timeoutId)
      lastError = err
      if (attempt < MAX_RETRIES) {
        await delay(RETRY_DELAY_MS * (attempt + 1))
        continue
      }
    }
  }

  if (lastError instanceof Error) {
    throw new OverpassError(
      lastError.name === 'AbortError'
        ? 'Overpass svarade inte i tid. Kontrollera din internetanslutning och försök igen.'
        : `Kunde inte hämta platser i närheten: ${lastError.message}`,
    )
  }
  throw new OverpassError('Kunde inte hämta platser i närheten.')
}

export async function fetchNearbyPois(
  trackId: string,
  lat: number,
  lng: number,
): Promise<Poi[]> {
  const cacheKey = `overpass:${trackId}`
  const cached = readCache<Poi[]>(cacheKey)
  if (cached) return cached

  const query = buildQuery(lat, lng)
  const data = await fetchOverpass(query)

  const seen = new Set<string>()
  const pois: Poi[] = []
  for (const el of data.elements) {
    const poi = elementToPoi(el, lat, lng)
    if (!poi || seen.has(poi.id)) continue
    seen.add(poi.id)
    pois.push(poi)
  }
  pois.sort((a, b) => a.distanceM - b.distanceM)

  writeCache(cacheKey, pois)
  return pois
}
