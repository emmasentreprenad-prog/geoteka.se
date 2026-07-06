import { useState, type ReactNode } from 'react'

export function BottomSheet({ children }: { children: ReactNode }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className={`bottom-sheet${expanded ? ' bottom-sheet-expanded' : ''}`}>
      <button
        type="button"
        className="bottom-sheet-handle"
        onClick={() => setExpanded((e) => !e)}
        aria-expanded={expanded}
        aria-label={expanded ? 'Minimera listan' : 'Visa hela listan'}
      >
        <span className="bottom-sheet-grip" />
      </button>
      <div className="bottom-sheet-content">{children}</div>
    </div>
  )
}
