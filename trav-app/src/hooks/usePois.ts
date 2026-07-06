import { useEffect, useState } from 'react'
import { fetchNearbyPois, OverpassError } from '../api/overpass'
import { applySponsors } from '../utils/sponsors'
import type { Poi } from '../types'

interface PoisState {
  pois: Poi[]
  loading: boolean
  error: string | null
}

export function usePois(trackId: string, lat: number, lng: number): PoisState & { retry: () => void } {
  const [state, setState] = useState<PoisState>({ pois: [], loading: true, error: null })
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    let cancelled = false
    setState({ pois: [], loading: true, error: null })

    fetchNearbyPois(trackId, lat, lng)
      .then((pois) => {
        if (cancelled) return
        setState({ pois: applySponsors(pois), loading: false, error: null })
      })
      .catch((err) => {
        if (cancelled) return
        const message =
          err instanceof OverpassError
            ? err.message
            : 'Något gick fel när platser i närheten skulle hämtas.'
        setState({ pois: [], loading: false, error: message })
      })

    return () => {
      cancelled = true
    }
  }, [trackId, lat, lng, retryCount])

  return { ...state, retry: () => setRetryCount((c) => c + 1) }
}
