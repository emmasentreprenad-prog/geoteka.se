import { useEffect, useRef } from 'react'
import { useGeolocation } from '../hooks/useGeolocation'
import { googleMapsDirectionsFromUrl, googleMapsDirectionsUrl } from '../utils/geo'

export function HitaHitButton({ lat, lng }: { lat: number; lng: number }) {
  const { lat: userLat, lng: userLng, loading, error, request } = useGeolocation()
  const pendingOpen = useRef(false)

  useEffect(() => {
    if (pendingOpen.current && userLat != null && userLng != null) {
      pendingOpen.current = false
      // Popup blockers reject window.open() once we're outside the synchronous click
      // handler (geolocation resolves asynchronously), so navigate the current tab instead.
      window.location.href = googleMapsDirectionsFromUrl(userLat, userLng, lat, lng)
    }
  }, [userLat, userLng, lat, lng])

  return (
    <div className="hitahit">
      <button
        type="button"
        className="btn btn-primary"
        onClick={() => {
          pendingOpen.current = true
          request()
        }}
        disabled={loading}
      >
        {loading ? 'Hämtar din position...' : '📍 Hitta hit'}
      </button>
      {error && (
        <p className="hitahit-fallback">
          {error}{' '}
          <a href={googleMapsDirectionsUrl(lat, lng)} target="_blank" rel="noopener noreferrer">
            Öppna vägbeskrivning ändå
          </a>
        </p>
      )}
    </div>
  )
}
