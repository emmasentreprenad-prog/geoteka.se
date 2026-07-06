import { useCallback, useState } from 'react'

interface GeolocationState {
  lat: number | null
  lng: number | null
  loading: boolean
  error: string | null
}

export function useGeolocation() {
  const [state, setState] = useState<GeolocationState>({
    lat: null,
    lng: null,
    loading: false,
    error: null,
  })

  const request = useCallback(() => {
    if (!navigator.geolocation) {
      setState({ lat: null, lng: null, loading: false, error: 'Din webbläsare stödjer inte platsdelning.' })
      return
    }

    setState((s) => ({ ...s, loading: true, error: null }))
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setState({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          loading: false,
          error: null,
        })
      },
      (err) => {
        const message =
          err.code === err.PERMISSION_DENIED
            ? 'Platsdelning nekades. Tillåt platsåtkomst för att använda funktionen.'
            : 'Kunde inte hämta din position just nu.'
        setState({ lat: null, lng: null, loading: false, error: message })
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 },
    )
  }, [])

  return { ...state, request }
}
