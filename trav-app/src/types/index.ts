export interface ParkingInfo {
  text: string
  lat?: number
  lng?: number
}

export interface EntranceInfo {
  lat: number
  lng: number
}

export interface Track {
  id: string
  name: string
  city: string
  lat: number
  lng: number
  website: string
  parking?: ParkingInfo
  entrance?: EntranceInfo
  capacity?: number
  trackLengthM?: number
  phone?: string
  openingHours?: string
}

export type PoiCategory =
  | 'hotel'
  | 'fast_food'
  | 'restaurant'
  | 'fuel'
  | 'supermarket'
  | 'mall'

export interface Poi {
  id: string
  category: PoiCategory
  name: string
  lat: number
  lng: number
  distanceM: number
  address?: string
  sponsored: boolean
}

export interface SponsorConfig {
  active: boolean
  chains: {
    category: PoiCategory
    names: string[]
    label: string
  }[]
}

export interface RaceDayTrack {
  trackId: string
  date: string
}

export interface CalendarDay {
  date: string
  trackIds: string[]
}
