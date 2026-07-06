import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import { useNavigate } from 'react-router-dom'
import type { Track } from '../types'
import { trackIcon } from '../utils/markerIcons'

const SWEDEN_CENTER: [number, number] = [62.5, 16.5]

function isTodayOrTomorrow(dateStr: string | undefined): boolean {
  if (!dateStr) return false
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(today.getDate() + 1)
  const toStr = (d: Date) => d.toISOString().slice(0, 10)
  return dateStr === toStr(today) || dateStr === toStr(tomorrow)
}

export function SwedenMap({
  tracks,
  nextRaceDate,
}: {
  tracks: Track[]
  nextRaceDate: Record<string, string>
}) {
  const navigate = useNavigate()

  return (
    <MapContainer center={SWEDEN_CENTER} zoom={5} className="sweden-map" scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {tracks.map((track) => {
        const highlighted = isTodayOrTomorrow(nextRaceDate[track.id])
        return (
          <Marker
            key={track.id}
            position={[track.lat, track.lng]}
            icon={trackIcon(highlighted)}
            eventHandlers={{ click: () => navigate(`/bana/${track.id}`) }}
          >
            <Popup>
              <strong>{track.name}</strong>
              <br />
              {track.city}
              {nextRaceDate[track.id] && (
                <>
                  <br />
                  Nästa tävlingsdag: {nextRaceDate[track.id]}
                </>
              )}
              <br />
              <button type="button" onClick={() => navigate(`/bana/${track.id}`)} className="btn btn-link">
                Visa bana →
              </button>
            </Popup>
          </Marker>
        )
      })}
    </MapContainer>
  )
}
