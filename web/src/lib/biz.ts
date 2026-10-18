import type { Facing, SeedDoc, ShelfLevel, SKU, Zone } from '@/types/seed'

/**
 * 业务图层：把 SpaceAnalyzer（Python 端）的计算镜像到前端，
 * 让 2D/3D 画布直接呈现「店主三问」：哪里最赚 / 哪里浪费 / 挪哪增收。
 * 销量用 ABC 速度代理，接真实 POS 后替换为预测接口（architecture §4.1）。
 */

const ABC_VELOCITY: Record<string, number> = { A: 14.0, B: 5.5, C: 1.75 }
const FRESH_BUMP = 1.15

export interface ZoneBiz {
  zone: Zone
  areaM2: number
  dailyMargin: number
  marginPerM2: number
  rank: number // 0 = 最高坪效
  facingCount: number
}

export interface FixtureBiz {
  fixtureId: string
  dailyMargin: number
  rank: number // 店内货架毛利排名
  isBottom: boolean // 含末位 10% 面位
  bottomFacings: string[]
}

export interface WhatIf {
  action: string
  facing_id: string
  zone: string
  from_sku: string
  to_sku: string
  to_sku_name: string
  delta_daily_margin_idr: number
}

export interface BizLayer {
  zones: ZoneBiz[]
  fixtures: Map<string, FixtureBiz>
  zoneById: Map<string, Zone>
  bottomFacingIds: Set<string>
  whatIf: WhatIf[]
  totalDailyMargin: number
  categoryMargins: { category: string; dailyMargin: number }[]
  skuMarginPerDay: (sku: SKU) => number
}

function polygonAreaM2(polygon: { x: number; y: number }[]): number {
  let s = 0
  for (let i = 0; i < polygon.length; i++) {
    const p1 = polygon[i]
    const p2 = polygon[(i + 1) % polygon.length]
    s += p1.x * p2.y - p2.x * p1.y
  }
  return Math.abs(s) / 2
}

function skuVelocity(sku: SKU): number {
  const cls = sku.abc_class ?? 'C'
  const v = ABC_VELOCITY[cls] ?? 1.75
  return v * (sku.fresh_flag ? FRESH_BUMP : 1)
}

function skuMarginRate(sku: SKU): number {
  if (sku.gross_margin != null) return sku.gross_margin
  return sku.unit_price > 0 ? (sku.unit_price - sku.unit_cost) / sku.unit_price : 0
}

export function skuDailyMargin(sku: SKU): number {
  return skuVelocity(sku) * sku.unit_price * skuMarginRate(sku)
}

export function computeBiz(doc: SeedDoc): BizLayer {
  const skuByCode = new Map(doc.skus.map((s) => [s.sku_code, s]))
  const fixtureZone = new Map(doc.fixtures.map((f) => [f.fixture_id, f.zone_id]))
  const levelFixture = new Map(doc.shelf_levels.map((sl: ShelfLevel) => [sl.shelf_level_id, sl.fixture_id]))
  const zoneById = new Map(doc.zones.map((z) => [z.zone_id, z]))

  // 面位 → 日毛利（heat 加权后参与 what-if）
  const facingRows = doc.facings
    .filter((fc: Facing) => fc.sku_code && skuByCode.has(fc.sku_code))
    .map((fc: Facing) => {
      const sku = skuByCode.get(fc.sku_code as string) as SKU
      const fixtureId = levelFixture.get(fc.shelf_level_id)
      const zone = zoneById.get(fixtureZone.get(fixtureId ?? '') ?? '')
      const daily = skuDailyMargin(sku)
      return {
        facingId: fc.facing_id,
        skuCode: fc.sku_code as string,
        skuName: sku.sku_name,
        category: sku.category_name,
        zoneId: zone?.zone_id ?? '',
        zoneName: zone?.zone_name ?? '未分区',
        heat: zone?.heat_value ?? 0.5,
        widthM: fc.facing_width_m,
        dailyMargin: daily,
        marginPerM: daily / Math.max(fc.facing_width_m, 0.01),
        weightedMargin: daily * (zone?.heat_value ?? 0.5),
      }
    })

  // 分区坪效
  const zoneAgg = new Map<string, { daily: number; facings: number }>()
  for (const r of facingRows) {
    const a = zoneAgg.get(r.zoneId) ?? { daily: 0, facings: 0 }
    a.daily += r.dailyMargin
    a.facings += 1
    zoneAgg.set(r.zoneId, a)
  }
  const zones: ZoneBiz[] = doc.zones.map((zone) => {
    const agg = zoneAgg.get(zone.zone_id) ?? { daily: 0, facings: 0 }
    const area = polygonAreaM2(zone.polygon)
    return {
      zone,
      areaM2: area,
      dailyMargin: agg.daily,
      marginPerM2: area > 0 ? agg.daily / area : 0,
      rank: 0,
      facingCount: agg.facings,
    }
  })
  const rankOrder = [...zones].sort((a, b) => b.marginPerM2 - a.marginPerM2)
  rankOrder.forEach((z, i) => {
    const target = zones.find((x) => x.zone.zone_id === z.zone.zone_id)
    if (target) target.rank = i
  })

  // 品类内效率 → 末位 10%
  const catVals = new Map<string, number[]>()
  for (const r of facingRows) {
    const arr = catVals.get(r.category) ?? []
    arr.push(r.marginPerM)
    catVals.set(r.category, arr)
  }
  const catMean = new Map<string, number>()
  catVals.forEach((arr, c) => catMean.set(c, arr.reduce((s, v) => s + v, 0) / arr.length))
  const withEff = facingRows.map((r) => ({
    ...r,
    efficiency: (r.marginPerM / (catMean.get(r.category) || 1)) || 1,
  }))
  const bottomN = Math.max(1, Math.floor(withEff.length * 0.1))
  const bottom = [...withEff].sort((a, b) => a.efficiency - b.efficiency).slice(0, bottomN)
  const bottomFacingIds = new Set(bottom.map((r) => r.facingId))

  // 货架级汇总
  const fixtureAgg = new Map<string, { daily: number; bottom: string[] }>()
  for (const r of facingRows) {
    const fixtureId = levelFixture.get(
      doc.facings.find((fc) => fc.facing_id === r.facingId)?.shelf_level_id ?? '',
    )
    if (!fixtureId) continue
    const a = fixtureAgg.get(fixtureId) ?? { daily: 0, bottom: [] }
    a.daily += r.dailyMargin
    if (bottomFacingIds.has(r.facingId)) a.bottom.push(r.facingId)
    fixtureAgg.set(fixtureId, a)
  }
  const fixtureRank = [...fixtureAgg.entries()].sort((a, b) => b[1].daily - a[1].daily)
  const rankMap = new Map(fixtureRank.map(([id], i) => [id, i]))
  const fixtures = new Map<string, FixtureBiz>()
  for (const [id, a] of fixtureAgg) {
    fixtures.set(id, {
      fixtureId: id,
      dailyMargin: a.daily,
      rank: rankMap.get(id) ?? 0,
      isBottom: a.bottom.length > 0,
      bottomFacings: a.bottom,
    })
  }

  // what-if：未上架 A/B 类高毛利候选 × 末位面位（贪心去重）
  const placed = new Set(facingRows.map((r) => r.skuCode))
  const candidates = doc.skus
    .filter((s) => !placed.has(s.sku_code) && (s.abc_class === 'A' || s.abc_class === 'B'))
    .sort((a, b) => skuDailyMargin(b) - skuDailyMargin(a))
  const usedTargets = new Set<string>()
  const whatIf: WhatIf[] = []
  for (const c of candidates) {
    const cMargin = skuDailyMargin(c)
    let best: { delta: number; target: (typeof withEff)[number] } | null = null
    for (const t of bottom) {
      if (usedTargets.has(t.facingId)) continue
      const delta = cMargin * t.heat - t.weightedMargin
      if (!best || delta > best.delta) best = { delta, target: t }
    }
    if (best && best.delta > 0) {
      usedTargets.add(best.target.facingId)
      whatIf.push({
        action: '替换面位',
        facing_id: best.target.facingId,
        zone: best.target.zoneName,
        from_sku: best.target.skuCode,
        to_sku: c.sku_code,
        to_sku_name: c.sku_name,
        delta_daily_margin_idr: Math.round(best.delta),
      })
      if (whatIf.length >= 3) break
    }
  }

  return {
    zones,
    fixtures,
    zoneById,
    bottomFacingIds,
    whatIf,
    totalDailyMargin: facingRows.reduce((s, r) => s + r.dailyMargin, 0),
    categoryMargins: [...catAgg(facingRows)],
    skuMarginPerDay: skuDailyMargin,
  }
}

function catAgg(rows: { category: string; dailyMargin: number }[]) {
  const m = new Map<string, number>()
  for (const r of rows) m.set(r.category, (m.get(r.category) ?? 0) + r.dailyMargin)
  return [...m.entries()]
    .map(([category, dailyMargin]) => ({ category, dailyMargin }))
    .sort((a, b) => b.dailyMargin - a.dailyMargin)
}

/**
 * 一键智能优化（贪心 MILP 的静态前端版）：
 * 对「品类内效率末位面位 × 未上架 A/B 高毛利 SKU」做全局正增量匹配，
 * 返回可应用到 facings 的方案与总增收潜力。
 */
export function optimizePlan(doc: SeedDoc, maxEdits = 20): {
  plan: Record<string, { sku_code: string; sku_name: string }>
  totalDelta: number
} {
  const skuByCode = new Map(doc.skus.map((s) => [s.sku_code, s]))
  const levelFixture = new Map(doc.shelf_levels.map((sl: ShelfLevel) => [sl.shelf_level_id, sl.fixture_id]))
  const fixtureZone = new Map(doc.fixtures.map((f) => [f.fixture_id, f.zone_id]))
  const zoneById = new Map(doc.zones.map((z) => [z.zone_id, z]))

  const facingRows = doc.facings
    .filter((fc: Facing) => fc.sku_code && skuByCode.has(fc.sku_code))
    .map((fc: Facing) => {
      const sku = skuByCode.get(fc.sku_code as string) as SKU
      const zone = zoneById.get(
        fixtureZone.get(levelFixture.get(fc.shelf_level_id) ?? '') ?? '',
      )
      const daily = skuDailyMargin(sku)
      return {
        facingId: fc.facing_id,
        skuCode: fc.sku_code as string,
        heat: zone?.heat_value ?? 0.5,
        widthM: fc.facing_width_m,
        dailyMargin: daily,
        marginPerM: daily / Math.max(fc.facing_width_m, 0.01),
        weightedMargin: daily * (zone?.heat_value ?? 0.5),
        category: sku.category_name,
      }
    })

  const catVals = new Map<string, number[]>()
  for (const r of facingRows) {
    const arr = catVals.get(r.category) ?? []
    arr.push(r.marginPerM)
    catVals.set(r.category, arr)
  }
  const catMean = new Map<string, number>()
  catVals.forEach((arr, c) => catMean.set(c, arr.reduce((s, v) => s + v, 0) / arr.length))
  const withEff = facingRows.map((r) => ({
    ...r,
    efficiency: r.marginPerM / (catMean.get(r.category) || 1) || 1,
  }))

  const placed = new Set(facingRows.map((r) => r.skuCode))
  const candidates = doc.skus
    .filter((s) => !placed.has(s.sku_code) && (s.abc_class === 'A' || s.abc_class === 'B'))
    .sort((a, b) => skuDailyMargin(b) - skuDailyMargin(a))
  const bottom = [...withEff].sort((a, b) => a.efficiency - b.efficiency)

  const plan: Record<string, { sku_code: string; sku_name: string }> = {}
  const usedTargets = new Set<string>()
  let totalDelta = 0
  for (const c of candidates) {
    if (Object.keys(plan).length >= maxEdits) break
    const cMargin = skuDailyMargin(c)
    for (const t of bottom) {
      if (usedTargets.has(t.facingId)) continue
      const delta = cMargin * t.heat - t.weightedMargin
      if (delta > 0) {
        usedTargets.add(t.facingId)
        plan[t.facingId] = { sku_code: c.sku_code, sku_name: c.sku_name }
        totalDelta += delta
        break
      }
    }
  }
  return { plan, totalDelta: Math.round(totalDelta) }
}

/** 坪效 → 连续色（单色相 emerald，透明度阶梯，Kimi 顺序色规范） */
export function zoneBizColor(rankRatio: number): string {
  // rankRatio 0（最高）→ 1（最低）
  const a = 0.42 - rankRatio * 0.34
  return `rgba(16, 185, 129, ${Math.max(a, 0.08).toFixed(2)})`
}

export function fmtIDR(v: number): string {
  if (v >= 1e9) return `Rp ${(v / 1e9).toFixed(1)} M`
  if (v >= 1e6) return `Rp ${(v / 1e6).toFixed(1)} jt`
  return `Rp ${Math.round(v).toLocaleString('id-ID')}`
}

/** 单个面位替换 SKU 的日毛利增量（拖拽沙盘实时计算用） */
export function facingDelta(doc: SeedDoc, facingId: string, newSkuCode: string): number {
  const fc = doc.facings.find((f) => f.facing_id === facingId)
  const sku = doc.skus.find((s) => s.sku_code === newSkuCode)
  if (!fc || !sku) return 0
  const level = doc.shelf_levels.find((l) => l.shelf_level_id === fc.shelf_level_id)
  const fixture = doc.fixtures.find((f) => f.fixture_id === level?.fixture_id)
  const zone = doc.zones.find((z) => z.zone_id === fixture?.zone_id)
  const heat = zone?.heat_value ?? 0.5
  const oldSku = fc.sku_code ? doc.skus.find((s) => s.sku_code === fc.sku_code) : null
  const oldMargin = oldSku ? skuDailyMargin(oldSku) * heat : 0
  return skuDailyMargin(sku) * heat - oldMargin
}
