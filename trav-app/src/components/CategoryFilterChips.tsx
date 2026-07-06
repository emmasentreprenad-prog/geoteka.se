import type { PoiCategory } from '../types'
import { CATEGORY_META, CATEGORY_ORDER } from '../utils/categoryMeta'

export function CategoryFilterChips({
  active,
  onToggle,
}: {
  active: Set<PoiCategory>
  onToggle: (category: PoiCategory) => void
}) {
  return (
    <div className="filter-chips" role="group" aria-label="Filtrera kategorier">
      {CATEGORY_ORDER.map((category) => {
        const meta = CATEGORY_META[category]
        const isActive = active.has(category)
        return (
          <button
            key={category}
            type="button"
            className={`chip${isActive ? ' chip-active' : ''}`}
            style={isActive ? { background: meta.color, borderColor: meta.color } : undefined}
            onClick={() => onToggle(category)}
            aria-pressed={isActive}
          >
            <span aria-hidden="true">{meta.emoji}</span> {meta.label}
          </button>
        )
      })}
    </div>
  )
}
