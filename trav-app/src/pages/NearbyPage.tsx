import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import tracksData from '../data/travbanor.json'
import type { Track } from '../types'
import { useGeolocation } from '../hooks/useGeolocation'
import { useCalendar } from '../hooks/useCalendar'
import { formatDistance, haversineDistanceM } from '../utils/geo'
import { LoadingSpinner } from '../components/LoadingSpinner'

const tracks = tracksData as Track[]
const RADIUS_M = 20 * 10_000 // 20 mil = 200 km

export function NearbyPage() {
  const { lat, lng, loading, error, request } = useGeolocation()
  const { nextRaceDate, loading: calendarLoading } = useCalendar()

  const nearby = useMemo(() => {
    if (lat == null || lng == null) return []
    return tracks
      .map((track) => ({
        track,
        distanceM: haversineDistanceM(lat, lng, track.lat, track.lng),
      }))
      .filter((t) => t.distanceM <= RADIUS_M)
      .sort((a, b) => {
        const dateA = nextRaceDate[a.track.id]
        const dateB = nextRaceDate[b.track.id]
        if (dateA && dateB) return dateA.localeCompare(dateB)
        if (dateA) return -1
        if (dateB) return 1
        return a.distanceM - b.distanceM
      })
  }, [lat, lng, nextRaceDate])

  return (
    <div className="nearby-page">
      <h2>Tävlingsdag nära dig</h2>
      <p>Visar travbanor inom 20 mil, sorterade på nästa tävlingsdatum.</p>

      {lat == null && (
        <button type="button" className="btn btn-primary" onClick={request} disabled={loading}>
          {loading ? 'Hämtar din position...' : '📍 Dela min position'}
        </button>
      )}
      {error && <p className="error-message">{error}</p>}

      {lat != null && calendarLoading && <LoadingSpinner label="Hämtar tävlingsdagar..." />}

      {lat != null && !calendarLoading && (
        <ul className="nearby-list">
          {nearby.map(({ track, distanceM }) => (
            <li key={track.id} className="nearby-item">
              <Link to={`/bana/${track.id}`}>
                <strong>{track.name}</strong> · {track.city}
              </Link>
              <div className="nearby-meta">
                {formatDistance(distanceM)} bort
                {nextRaceDate[track.id] && <> · Nästa tävlingsdag: {nextRaceDate[track.id]}</>}
                {!nextRaceDate[track.id] && <> · Ingen tävlingsdag inom 30 dagar</>}
              </div>
            </li>
          ))}
          {nearby.length === 0 && <li>Inga travbanor hittades inom 20 mil.</li>}
        </ul>
      )}
    </div>
  )
}
