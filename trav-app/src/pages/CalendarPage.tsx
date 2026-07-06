import { Link } from 'react-router-dom'
import tracksData from '../data/travbanor.json'
import type { Track } from '../types'
import { useCalendar } from '../hooks/useCalendar'
import { LoadingSpinner } from '../components/LoadingSpinner'

const tracks = tracksData as Track[]
const trackById = new Map(tracks.map((t) => [t.id, t]))

function formatDateLabel(dateStr: string): string {
  const date = new Date(`${dateStr}T00:00:00`)
  return date.toLocaleDateString('sv-SE', { weekday: 'long', day: 'numeric', month: 'long' })
}

export function CalendarPage() {
  const { byDate, loading } = useCalendar()
  const dates = Object.keys(byDate).sort()

  return (
    <div className="calendar-page">
      <h2>Tävlingskalender – kommande 30 dagar</h2>
      {loading && <LoadingSpinner label="Hämtar tävlingsdagar..." />}
      {!loading && dates.length === 0 && (
        <p className="calendar-empty">
          Kunde inte hämta tävlingsdagar just nu. Prova gå in på en enskild bana istället.
        </p>
      )}
      <ul className="calendar-list">
        {dates.map((date) => (
          <li key={date} className="calendar-day">
            <div className="calendar-date">{formatDateLabel(date)}</div>
            <ul className="calendar-tracks">
              {byDate[date].map((trackId) => {
                const track = trackById.get(trackId)
                if (!track) return null
                return (
                  <li key={trackId}>
                    <Link to={`/bana/${trackId}`}>{track.name}</Link> · {track.city}
                  </li>
                )
              })}
            </ul>
          </li>
        ))}
      </ul>
    </div>
  )
}
