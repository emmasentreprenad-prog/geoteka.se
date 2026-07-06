import L from 'leaflet'

export function makeDivIcon(opts: {
  emoji: string
  color: string
  size?: number
  highlighted?: boolean
}): L.DivIcon {
  const size = opts.size ?? 32
  const ring = opts.highlighted ? '0 0 0 4px rgba(255,196,0,0.65)' : '0 1px 4px rgba(0,0,0,0.4)'
  return L.divIcon({
    className: 'poi-div-icon',
    html: `<div style="
      width:${size}px;height:${size}px;border-radius:50%;
      background:${opts.color};display:flex;align-items:center;justify-content:center;
      font-size:${Math.round(size * 0.55)}px;box-shadow:${ring};border:2px solid white;
    ">${opts.emoji}</div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  })
}

export const trackIcon = (highlighted: boolean) =>
  makeDivIcon({ emoji: '🏇', color: highlighted ? '#c62828' : '#22496b', size: highlighted ? 40 : 34, highlighted })

export const userIcon = () => makeDivIcon({ emoji: '📍', color: '#111827', size: 30 })
