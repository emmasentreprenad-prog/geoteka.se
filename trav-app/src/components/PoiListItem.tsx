import type { Poi } from '../types'
import { CATEGORY_META } from '../utils/categoryMeta'
import { formatDistance, googleMapsDirectionsUrl } from '../utils/geo'
import { sponsorLabelFor } from '../utils/sponsors'

export function PoiListItem({ poi, onSelect }: { poi: Poi; onSelect?: () => void }) {
  const meta = CATEGORY_META[poi.category]
  const sponsorLabel = sponsorLabelFor(poi)

  return (
    <li className={`poi-item${poi.sponsored ? ' poi-item-sponsored' : ''}`}>
      <button type="button" className="poi-item-main" onClick={onSelect}>
        <span className="poi-icon" style={{ background: meta.color }} aria-hidden="true">
          {meta.emoji}
        </span>
        <span className="poi-info">
          <span className="poi-name">
            {poi.name}
            {sponsorLabel && <span className="sponsor-badge">{sponsorLabel}</span>}
          </span>
          <span className="poi-meta">
            {meta.label} · {formatDistance(poi.distanceM)}
          </span>
        </span>
      </button>
      <a
        href={googleMapsDirectionsUrl(poi.lat, poi.lng)}
        target="_blank"
        rel="noopener noreferrer"
        className="btn btn-directions"
      >
        Vägbeskrivning
      </a>
    </li>
  )
}
