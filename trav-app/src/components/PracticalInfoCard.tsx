import type { Track } from '../types'
import { googleMapsDirectionsUrl } from '../utils/geo'

export function PracticalInfoCard({ track }: { track: Track }) {
  const hasAnyInfo =
    track.parking ||
    track.entrance ||
    track.capacity ||
    track.trackLengthM ||
    track.phone ||
    track.openingHours

  if (!hasAnyInfo) return null

  return (
    <div className="practical-info-card">
      <h3>Praktisk info</h3>
      <dl>
        {track.trackLengthM && (
          <div className="info-row">
            <dt>Banlängd</dt>
            <dd>{track.trackLengthM} m</dd>
          </div>
        )}
        {track.capacity && (
          <div className="info-row">
            <dt>Publikkapacitet</dt>
            <dd>{track.capacity.toLocaleString('sv-SE')} personer</dd>
          </div>
        )}
        {track.phone && (
          <div className="info-row">
            <dt>Telefon</dt>
            <dd>
              <a href={`tel:${track.phone.replace(/\s/g, '')}`}>{track.phone}</a>
            </dd>
          </div>
        )}
        {track.openingHours && (
          <div className="info-row">
            <dt>Öppettider</dt>
            <dd>{track.openingHours}</dd>
          </div>
        )}
        {track.parking && (
          <div className="info-row">
            <dt>Parkering</dt>
            <dd>
              {track.parking.text}
              {track.parking.lat != null && track.parking.lng != null && (
                <>
                  {' '}
                  <a
                    href={googleMapsDirectionsUrl(track.parking.lat, track.parking.lng)}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Vägbeskrivning till parkering →
                  </a>
                </>
              )}
            </dd>
          </div>
        )}
      </dl>
    </div>
  )
}
