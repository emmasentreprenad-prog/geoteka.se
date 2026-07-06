import { useMemo, useState } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
import tracksData from '../data/travbanor.json'
import type { PoiCategory, Track } from '../types'
import { TrackDetailMap } from '../components/TrackDetailMap'
import { CategoryFilterChips } from '../components/CategoryFilterChips'
import { PoiListItem } from '../components/PoiListItem'
import { BottomSheet } from '../components/BottomSheet'
import { PracticalInfoCard } from '../components/PracticalInfoCard'
import { HitaHitButton } from '../components/HitaHitButton'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'
import { usePois } from '../hooks/usePois'
import { useCalendar } from '../hooks/useCalendar'
import { CATEGORY_ORDER } from '../utils/categoryMeta'

const tracks = tracksData as Track[]

export function TrackPage() {
  const { trackId } = useParams<{ trackId: string }>()
  const track = tracks.find((t) => t.id === trackId)
  const [activeCategories, setActiveCategories] = useState<Set<PoiCategory>>(
    new Set(CATEGORY_ORDER),
  )
  const [selectedPoiId, setSelectedPoiId] = useState<string | null>(null)

  const { pois, loading, error, retry } = usePois(
    track?.id ?? '',
    track?.lat ?? 0,
    track?.lng ?? 0,
  )
  const { nextRaceDate } = useCalendar()

  const filteredPois = useMemo(
    () => pois.filter((p) => activeCategories.has(p.category)),
    [pois, activeCategories],
  )

  if (!track) return <Navigate to="/" replace />

  function toggleCategory(category: PoiCategory) {
    setActiveCategories((prev) => {
      const next = new Set(prev)
      if (next.has(category)) next.delete(category)
      else next.add(category)
      return next
    })
  }

  const listContent = (
    <>
      <CategoryFilterChips active={activeCategories} onToggle={toggleCategory} />
      {loading && <LoadingSpinner label="Hämtar platser i närheten..." />}
      {error && <ErrorMessage message={error} onRetry={retry} />}
      {!loading && !error && (
        <ul className="poi-list">
          {filteredPois.map((poi) => (
            <PoiListItem key={poi.id} poi={poi} onSelect={() => setSelectedPoiId(poi.id)} />
          ))}
          {filteredPois.length === 0 && <li className="poi-list-empty">Inga platser hittades i denna kategori.</li>}
        </ul>
      )}
    </>
  )

  return (
    <div className="track-page">
      <div className="track-page-header">
        <Link to="/" className="back-link">
          ← Alla banor
        </Link>
        <h2>{track.name}</h2>
        <p className="track-city">{track.city}</p>
        {nextRaceDate[track.id] && <p className="next-race">Nästa tävlingsdag: {nextRaceDate[track.id]}</p>}
        <div className="track-page-actions">
          <HitaHitButton lat={track.lat} lng={track.lng} />
          <a href={track.website} target="_blank" rel="noopener noreferrer" className="btn btn-secondary">
            Webbplats →
          </a>
        </div>
        <PracticalInfoCard track={track} />
      </div>

      <div className="track-page-map-area">
        <TrackDetailMap track={track} pois={filteredPois} selectedPoiId={selectedPoiId} />
      </div>

      <div className="track-page-list-desktop">{listContent}</div>
      <BottomSheet>{listContent}</BottomSheet>
    </div>
  )
}
