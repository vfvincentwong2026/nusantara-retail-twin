import type { SeedDoc } from '@/types/seed'

export const STORE_SIZES = [500, 2000, 5000] as const

export async function loadSeed(size: number): Promise<SeedDoc> {
  const res = await fetch(`${import.meta.env.BASE_URL}seeds/store_${size}sqm_demo.json`)
  if (!res.ok) throw new Error(`种子数据加载失败：${res.status}`)
  return (await res.json()) as SeedDoc
}

// heat 0(冷) → 1(热) 的色带：蓝 → 青 → 黄 → 红
export function heatColor(heat: number, alpha = 1): string {
  const h = Math.max(0, Math.min(1, heat))
  const hue = 210 - h * 210 // 210(blue) → 0(red)
  return `hsla(${hue}, 75%, 55%, ${alpha})`
}

export const ZONE_TYPE_LABEL: Record<string, string> = {
  fresh: '生鲜',
  ambient: '常温',
  frozen: '冷冻',
  household: '日用家居',
  fashion: '服饰',
  promo: '促销',
  checkout: '收银',
}

export const FIXTURE_TYPE_LABEL: Record<string, string> = {
  gondola: '中岛货架',
  shelf: '壁柜',
  cooler: '冷柜',
  freezer: '冷冻柜',
  meat_counter: '鲜肉柜',
  seafood_counter: '海鲜柜',
  produce_rack: '果蔬架',
  bakery_counter: '烘焙柜',
  hot_food_counter: '热食柜',
}

export const FIXTURE_TYPE_COLOR: Record<string, string> = {
  gondola: '#94a3b8',
  shelf: '#a78bfa',
  cooler: '#38bdf8',
  freezer: '#818cf8',
  meat_counter: '#f87171',
  seafood_counter: '#2dd4bf',
  produce_rack: '#4ade80',
  bakery_counter: '#fbbf24',
  hot_food_counter: '#fb923c',
}

export function footprintOf(doc: SeedDoc): { minX: number; minY: number; width: number; height: number } {
  const xs = doc.zones.flatMap((z) => z.polygon.map((p) => p.x))
  const ys = doc.zones.flatMap((z) => z.polygon.map((p) => p.y))
  const minX = Math.min(...xs)
  const minY = Math.min(...ys)
  return { minX, minY, width: Math.max(...xs) - minX, height: Math.max(...ys) - minY }
}

export function formatIDR(v: number): string {
  return 'Rp ' + v.toLocaleString('id-ID')
}

export function downloadJSON(data: unknown, filename: string): void {
  const blob = new Blob([JSON.stringify(data, null, 1)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
