import { useEffect, useState } from 'react'
import { fetchCalendarRange, type CalendarRange } from '../api/atg'

interface CalendarState extends CalendarRange {
  loading: boolean
}

const EMPTY: CalendarRange = { byDate: {}, nextRaceDate: {} }

let cachedPromise: Promise<CalendarRange> | null = null

/** Shared across all consumers so the 30-day calendar sweep only runs once per session. */
export function useCalendar(): CalendarState {
  const [state, setState] = useState<CalendarState>({ ...EMPTY, loading: true })

  useEffect(() => {
    let cancelled = false
    if (!cachedPromise) cachedPromise = fetchCalendarRange(30)

    cachedPromise
      .then((range) => {
        if (!cancelled) setState({ ...range, loading: false })
      })
      .catch(() => {
        if (!cancelled) setState({ ...EMPTY, loading: false })
      })

    return () => {
      cancelled = true
    }
  }, [])

  return state
}
