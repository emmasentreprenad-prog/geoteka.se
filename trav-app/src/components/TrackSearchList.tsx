import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import type { Track } from '../types'

export function TrackSearchList({
  tracks,
  nextRaceDate,
}: {
  tracks: Track[]
  nextRaceDate: Record<string, string>
}) {
  const [query, setQuery] = useState('')

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    const list = q
      ? tracks.filter(
          (t) => t.name.toLowerCase().includes(q) || t.city.toLowerCase().includes(q),
        )
      : tracks
    return [...list].sort((a, b) => a.name.localeCompare(b.name, 'sv'))
  }, [tracks, query])

  return (
    <div className="track-search-list">
      <input
        type="search"
        placeholder="Sök travbana eller ort..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="search-input"
        aria-label="Sök travbana"
      />
      <ul className="track-list">
        {filtered.map((track) => (
          <li key={track.id}>
            <Link to={`/bana/${track.id}`} className="track-list-item">
              <span className="track-list-name">{track.name}</span>
              <span className="track-list-city">{track.city}</span>
              {nextRaceDate[track.id] && (
                <span className="track-list-race-date">Nästa tävling: {nextRaceDate[track.id]}</span>
              )}
            </Link>
          </li>
        ))}
        {filtered.length === 0 && <li className="track-list-empty">Inga banor matchade sökningen.</li>}
      </ul>
    </div>
  )
}
