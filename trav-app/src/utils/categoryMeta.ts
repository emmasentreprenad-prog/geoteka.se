import type { PoiCategory } from '../types'

export interface CategoryMeta {
  label: string
  emoji: string
  color: string
}

export const CATEGORY_META: Record<PoiCategory, CategoryMeta> = {
  hotel: { label: 'Hotell', emoji: '🏨', color: '#6d4aa8' },
  fast_food: { label: 'Snabbmat', emoji: '🍔', color: '#e07a1f' },
  restaurant: { label: 'Restaurang', emoji: '🍽️', color: '#c23a5e' },
  fuel: { label: 'Bensinstation', emoji: '⛽', color: '#2f7a3d' },
  supermarket: { label: 'Livsmedel', emoji: '🛒', color: '#1f6fa8' },
  mall: { label: 'Köpcentrum', emoji: '🏬', color: '#8a6d1f' },
}

export const CATEGORY_ORDER: PoiCategory[] = [
  'hotel',
  'restaurant',
  'fast_food',
  'supermarket',
  'mall',
  'fuel',
]
