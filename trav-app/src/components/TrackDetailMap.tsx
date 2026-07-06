import { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import type { Map as LeafletMap } from 'leaflet'
import type { Poi, Track } from '../types'
import { CATEGORY_META } from '../utils/categoryMeta'
import { makeDivIcon, trackIcon } from '../utils/markerIcons'
import { formatDistance, googleMapsDirectionsUrl } from '../utils/geo'
import { sponsorLabelFor } from '../utils/sponsors'

function FlyToTrack({ lat, lng }: { lat: number; lng: number }) {
  const map = useMap()
  useEffect(() => {
    map.flyTo([lat, lng], 13, { duration: 0.6 })
  }, [lat, lng, map])
  return null
}

export function TrackDetailMap({
  track,
  pois,
  selectedPoiId,
}: {
  track: Track
  pois: Poi[]
  selectedPoiId: string | null
}) {
  const mapRef = useRef<LeafletMap | null>(null)

  return (
    <MapContainer
      center={[track.lat, track.lng]}
      zoom={13}
      className="track-map"
      scrollWheelZoom
      ref={mapRef}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FlyToTrack lat={track.lat} lng={track.lng} />
      <Marker position={[track.lat, track.lng]} icon={trackIcon(false)}>
        <Popup>
          <strong>{track.name}</strong>
          <br />
          {track.city}
        </Popup>
      </Marker>
      {pois.map((poi) => {
        const meta = CATEGORY_META[poi.category]
        return (
          <Marker
            key={poi.id}
            position={[poi.lat, poi.lng]}
            icon={makeDivIcon({
              emoji: meta.emoji,
              color: meta.color,
              size: poi.sponsored ? 30 : 24,
              highlighted: poi.id === selectedPoiId || poi.sponsored,
            })}
          >
            <Popup>
              <strong>{poi.name}</strong>
              {sponsorLabelFor(poi) && <div className="sponsor-badge">{sponsorLabelFor(poi)}</div>}
              <br />
              {meta.label} · {formatDistance(poi.distanceM)} från banan
              <br />
              <a
                href={googleMapsDirectionsUrl(poi.lat, poi.lng)}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-link"
              >
                Vägbeskrivning →
              </a>
            </Popup>
          </Marker>
        )
      })}
    </MapContainer>
  )
}
