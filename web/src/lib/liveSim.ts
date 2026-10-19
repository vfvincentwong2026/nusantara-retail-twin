import { useEffect, useMemo, useRef, useState } from 'react'
import type { SeedDoc } from '@/types/seed'

export interface Tx {
  id: number
  time: string
  skuName: string
  qty: number
  margin: number
  zoneName: string
}

export interface LiveSim {
  todayMargin: number
  txCount: number
  customers: number
  log: Tx[]
  zoneLive: Record<string, number>
}

const EMPTY: LiveSim = { todayMargin: 0, txCount: 0, customers: 34, log: [], zoneLive: {} }

/**
 * 实时经营模拟：按 SKU 速度加权的随机成交（洽谈演示用，接 POS 后替换为真实数据流）。
 * 提升到 App 层共享：大屏显示流水，2D 平面图按分区闪脉冲。
 */
export function useLiveSim(doc: SeedDoc | null): LiveSim {
  const skus = useMemo(
    () =>
      (doc?.skus ?? [])
        .map((s) => ({ s, w: (s.abc_class === 'A' ? 14 : s.abc_class === 'B' ? 5.5 : 1.75) * (s.fresh_flag ? 1.15 : 1) }))
        .filter((x) => x.s.unit_price > 0),
    [doc],
  )
  // SKU → 可选分区（经面位 → 货架层 → 货架 → 分区解析）
  const skuZones = useMemo(() => {
    const m = new Map<string, string[]>()
    if (!doc) return m
    const levelFixture = new Map(doc.shelf_levels.map((l) => [l.shelf_level_id, l.fixture_id]))
    const fixtureZone = new Map(doc.fixtures.map((f) => [f.fixture_id, f.zone_id]))
    const zoneName = new Map(doc.zones.map((z) => [z.zone_id, z.zone_name]))
    for (const fc of doc.facings) {
      if (!fc.sku_code) continue
      const zn = zoneName.get(fixtureZone.get(levelFixture.get(fc.shelf_level_id) ?? '') ?? '')
      if (!zn) continue
      const arr = m.get(fc.sku_code) ?? []
      if (!arr.includes(zn)) arr.push(zn)
      m.set(fc.sku_code, arr)
    }
    return m
  }, [doc])
  const totalW = skus.reduce((a, x) => a + x.w, 0)
  const pick = () => {
    let r = Math.random() * totalW
    for (const x of skus) {
      r -= x.w
      if (r <= 0) return x.s
    }
    return skus[skus.length - 1]?.s
  }
  const [sim, setSim] = useState<LiveSim>(EMPTY)
  const idRef = useRef(0)
  useEffect(() => {
    if (!doc || skus.length === 0) return
    const t = setInterval(() => {
      const sku = pick()
      if (!sku) return
      const rate = sku.gross_margin ?? (sku.unit_price > 0 ? (sku.unit_price - sku.unit_cost) / sku.unit_price : 0)
      const qty = 1 + Math.floor(Math.random() * 3)
      const margin = sku.unit_price * rate * qty
      const zones = skuZones.get(sku.sku_code)
      const zoneName = zones?.[Math.floor(Math.random() * (zones?.length ?? 0))] ?? '未分区'
      const now = new Date()
      idRef.current += 1
      setSim((prev) => ({
        todayMargin: prev.todayMargin + margin,
        txCount: prev.txCount + 1,
        customers: Math.max(8, Math.min(120, prev.customers + Math.floor(Math.random() * 9) - 4)),
        zoneLive: { ...prev.zoneLive, [zoneName]: (prev.zoneLive[zoneName] ?? 0) + margin },
        log: [
          { id: idRef.current, time: now.toTimeString().slice(0, 8), skuName: sku.sku_name, qty, margin, zoneName },
          ...prev.log,
        ].slice(0, 7),
      }))
    }, 1800)
    return () => clearInterval(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc])
  return sim
}
