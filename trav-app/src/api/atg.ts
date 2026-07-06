import tracksData from '../data/travbanor.json'
import type { Track } from '../types'
import { readCache, writeCache } from '../utils/sessionCache'

const CALENDAR_ENDPOINT = 'https://www.atg.se/services/racinginfo/v1/api/calendar/day'
const REQUEST_TIMEOUT_MS = 8000
const NO_DATA_SENTINEL = '__none__'

const tracks = tracksData as Track[]

function normalize(name: string): string {
  return name
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/\b(travbana|travet|trav)\b/g, '')
    .replace(/[^a-z0-9]/g, '')
}

const trackByNormalizedName = new Map(
  tracks.map((t) => [normalize(t.name), t.id]),
)

/**
 * ATG's racinginfo API is undocumented and its response shape is not
 * guaranteed, so instead of trusting a fixed schema we walk the whole
 * JSON tree looking for strings that match a known track name. This is
 * resilient to the API changing its nesting as long as track names still
 * appear somewhere in the payload.
 */
function findTrackIdsInPayload(value: unknown, found: Set<string>): void {
  if (typeof value === 'string') {
    const id = trackByNormalizedName.get(normalize(value))
    if (id) found.add(id)
    return
  }
  if (Array.isArray(value)) {
    for (const item of value) findTrackIdsInPayload(item, found)
    return
  }
  if (value && typeof value === 'object') {
    for (const v of Object.values(value)) findTrackIdsInPayload(v, found)
  }
}

async function fetchCalendarDayTrackIds(date: string): Promise<string[]> {
  const cacheKey = `atg-calendar:${date}`
  const cached = readCache<string[] | typeof NO_DATA_SENTINEL>(cacheKey)
  if (cached !== null) return cached === NO_DATA_SENTINEL ? [] : cached

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

  try {
    const response = await fetch(`${CALENDAR_ENDPOINT}/${date}`, {
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    })
    if (!response.ok) {
      writeCache(cacheKey, NO_DATA_SENTINEL)
      return []
    }
    const data: unknown = await response.json()
    const found = new Set<string>()
    findTrackIdsInPayload(data, found)
    const result = Array.from(found)
    writeCache(cacheKey, result)
    return result
  } catch {
    // Network error, timeout, CORS block, or malformed JSON — the calendar
    // is an optional enhancement, so we fail silently and cache the miss.
    writeCache(cacheKey, NO_DATA_SENTINEL)
    return []
  } finally {
    clearTimeout(timeoutId)
  }
}

function toDateString(d: Date): string {
  return d.toISOString().slice(0, 10)
}

export interface CalendarRange {
  /** date (YYYY-MM-DD) -> track ids racing that day */
  byDate: Record<string, string[]>
  /** track id -> nearest upcoming race date within the fetched range */
  nextRaceDate: Record<string, string>
}

/** Sweeps the next `daysAhead` days of the ATG calendar, one request per date. */
export async function fetchCalendarRange(daysAhead = 30): Promise<CalendarRange> {
  const byDate: Record<string, string[]> = {}
  const nextRaceDate: Record<string, string> = {}
  const today = new Date()

  for (let i = 0; i < daysAhead; i++) {
    const day = new Date(today)
    day.setDate(day.getDate() + i)
    const dateStr = toDateString(day)

    const trackIds = await fetchCalendarDayTrackIds(dateStr)
    if (trackIds.length > 0) byDate[dateStr] = trackIds
    for (const id of trackIds) {
      if (!(id in nextRaceDate)) nextRaceDate[id] = dateStr
    }
  }

  return { byDate, nextRaceDate }
}
