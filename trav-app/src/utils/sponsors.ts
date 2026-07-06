import sponsorsConfig from '../data/sponsors.json'
import type { Poi, SponsorConfig } from '../types'

const config = sponsorsConfig as SponsorConfig

export function applySponsors(pois: Poi[]): Poi[] {
  if (!config.active) return pois

  const sponsored = pois.map((poi) => {
    const chain = config.chains.find(
      (c) =>
        c.category === poi.category &&
        c.names.some((n) => poi.name.toLowerCase().includes(n.toLowerCase())),
    )
    return chain ? { ...poi, sponsored: true } : poi
  })

  return sponsored.sort((a, b) => {
    if (a.sponsored !== b.sponsored) return a.sponsored ? -1 : 1
    return a.distanceM - b.distanceM
  })
}

export function sponsorLabelFor(poi: Poi): string | undefined {
  if (!poi.sponsored) return undefined
  const chain = config.chains.find(
    (c) =>
      c.category === poi.category &&
      c.names.some((n) => poi.name.toLowerCase().includes(n.toLowerCase())),
  )
  return chain?.label
}
