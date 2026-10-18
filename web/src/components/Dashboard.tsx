import { useEffect, useMemo, useRef, useState } from 'react'
import type { FacingEdit, SeedDoc } from '@/types/seed'
import { computeBiz, fmtIDR, optimizePlan, type BizLayer } from '@/lib/biz'
import { toast } from 'sonner'

interface Tx {
  id: number
  time: string
  skuName: string
  qty: number
  margin: number
}

/** 实时经营模拟：按 SKU 速度加权的随机成交，驱动大屏「活」起来（洽谈演示用，接 POS 后替换） */
function useLiveSim(doc: SeedDoc) {
  const skus = useMemo(
    () =>
      doc.skus
        .map((s) => ({ s, w: (s.abc_class === 'A' ? 14 : s.abc_class === 'B' ? 5.5 : 1.75) * (s.fresh_flag ? 1.15 : 1) }))
        .filter((x) => x.s.unit_price > 0),
    [doc],
  )
  const totalW = skus.reduce((a, x) => a + x.w, 0)
  const pick = () => {
    let r = Math.random() * totalW
    for (const x of skus) {
      r -= x.w
      if (r <= 0) return x.s
    }
    return skus[skus.length - 1]?.s
  }
  const [sim, setSim] = useState({ todayMargin: 0, txCount: 0, customers: 34, log: [] as Tx[] })
  const idRef = useRef(0)
  useEffect(() => {
    const t = setInterval(() => {
      const sku = pick()
      if (!sku) return
      const rate = sku.gross_margin ?? (sku.unit_price > 0 ? (sku.unit_price - sku.unit_cost) / sku.unit_price : 0)
      const qty = 1 + Math.floor(Math.random() * 3)
      const margin = sku.unit_price * rate * qty
      const now = new Date()
      idRef.current += 1
      setSim((prev) => ({
        todayMargin: prev.todayMargin + margin,
        txCount: prev.txCount + 1,
        customers: Math.max(8, Math.min(120, prev.customers + Math.floor(Math.random() * 9) - 4)),
        log: [
          { id: idRef.current, time: now.toTimeString().slice(0, 8), skuName: sku.sku_name, qty, margin },
          ...prev.log,
        ].slice(0, 7),
      }))
    }, 1800)
    return () => clearInterval(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc])
  return sim
}

/**
 * 经营数据大屏：与 2D/3D 孪生对应的第三视图。
 * 面向店主的「一眼看见钱」——KPI 大数字 + 分区坪效 + 品类毛利 + 末位警示 + 一键优化。
 */
export function Dashboard({
  doc,
  biz,
  onApplyPlan,
}: {
  doc: SeedDoc
  biz: BizLayer
  onApplyPlan: (edits: Record<string, FacingEdit>) => void
}) {
  const [busy, setBusy] = useState(false)
  const sim = useLiveSim(doc)
  const [clock, setClock] = useState(() => new Date().toTimeString().slice(0, 8))
  useEffect(() => {
    const t = setInterval(() => setClock(new Date().toTimeString().slice(0, 8)), 1000)
    return () => clearInterval(t)
  }, [])

  // 优化预览：直接基于当前 doc 算一遍（含已挂 edits 的商品占位）
  const preview = useMemo(() => {
    const { plan, totalDelta } = optimizePlan(doc)
    return { plan, totalDelta, count: Object.keys(plan).length }
  }, [doc])

  const runOptimize = () => {
    setBusy(true)
    const edits: Record<string, FacingEdit> = {}
    for (const [facingId, s] of Object.entries(preview.plan)) {
      const fc = doc.facings.find((f) => f.facing_id === facingId)
      edits[facingId] = { sku_code: s.sku_code, max_units: fc?.max_units ?? 1 }
    }
    onApplyPlan(edits)
    toast.success(`全店智能优化：${preview.count} 个面位，+${fmtIDR(preview.totalDelta)}/hari`)
    setBusy(false)
  }

  const kpis: { label: string; value: string; accent?: string; live?: boolean }[] = [
    { label: '今日实时毛利（模拟 POS）', value: fmtIDR(sim.todayMargin), accent: 'text-emerald-400', live: true },
    { label: '成交笔数', value: String(sim.txCount), live: true },
    { label: '当前在店客流', value: `${sim.customers} 人`, live: true },
    { label: '坪效最佳分区', value: biz.zones.find((z) => z.rank === 0)?.zone.zone_name ?? '—' },
    { label: '末位面位（品类内）', value: String(biz.bottomFacingIds.size), accent: 'text-amber-400' },
    {
      label: '挪位增收潜力',
      value: `+${fmtIDR(preview.totalDelta)}/hari`,
      accent: 'text-emerald-400',
    },
  ]

  const zoneBars = [...biz.zones].sort((a, b) => b.marginPerM2 - a.marginPerM2)
  const maxZone = Math.max(...zoneBars.map((z) => z.marginPerM2), 1)
  const cats = biz.categoryMargins.slice(0, 8)
  const maxCat = Math.max(...cats.map((c) => c.dailyMargin), 1)

  // 验证：优化后毛利是否确实提升（用改动后的 doc 重算）
  const verifiedDelta = useMemo(() => {
    const facings = doc.facings.map((fc) => {
      const p = preview.plan[fc.facing_id]
      return p ? { ...fc, sku_code: p.sku_code } : fc
    })
    return computeBiz({ ...doc, facings }).totalDailyMargin - biz.totalDailyMargin
  }, [doc, preview, biz])

  return (
    <div className="h-full overflow-y-auto rounded-lg border ds-hairline bg-slate-950 p-4">
      {/* 顶条 */}
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="flex items-center gap-2 text-sm font-semibold tracking-wide">
            经营数据大屏
            <span className="flex items-center gap-1 rounded border border-emerald-500/40 bg-emerald-500/10 px-1.5 py-0.5 text-[9px] font-medium tracking-widest text-emerald-400">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
              LIVE
            </span>
            <span className="num text-[11px] font-normal text-slate-500">{clock}</span>
          </h2>
          <p className="text-[11px] text-slate-500">数字孪生实时核算 · 坪效 / 品类 / 末位 / 优化</p>
        </div>
        <button
          onClick={runOptimize}
          disabled={busy || preview.count === 0}
          className="flex items-center gap-2 rounded-md bg-emerald-500/15 border border-emerald-500/40 px-3.5 py-1.5 text-xs font-medium text-emerald-300 transition-colors hover:bg-emerald-500/25 disabled:opacity-40"
        >
          ⚡ 一键智能优化（贪心 MILP）
        </button>
      </div>

      {/* KPI 行 */}
      <div className="grid grid-cols-3 gap-2 md:grid-cols-6">
        {kpis.map((k) => (
          <div key={k.label} className="rounded-lg border ds-hairline bg-slate-900/60 px-3 py-2.5">
            <p className="flex items-center gap-1.5 text-[10px] uppercase tracking-wide text-slate-500">
              {k.label}
              {k.live && <span className="h-1 w-1 animate-pulse rounded-full bg-emerald-400" />}
            </p>
            <p key={k.value} className={`num mt-1 animate-pulse text-lg font-semibold ${k.accent ?? 'text-slate-100'}`}>{k.value}</p>
          </div>
        ))}
      </div>

      <div className="mt-3 grid gap-3 lg:grid-cols-2">
        {/* 分区坪效 */}
        <section className="rounded-lg border ds-hairline bg-slate-900/60 p-3.5">
          <h3 className="mb-3 text-xs font-medium text-slate-400">分区坪效（毛利 / m² / 日）</h3>
          <div className="space-y-2">
            {zoneBars.map((z) => (
              <div key={z.zone.zone_id} className="flex items-center gap-2">
                <span className="w-24 shrink-0 truncate text-[11px] text-slate-300">{z.zone.zone_name}</span>
                <div className="h-4 flex-1 overflow-hidden rounded-sm bg-slate-800">
                  <div
                    className="h-full rounded-sm"
                    style={{
                      width: `${(z.marginPerM2 / maxZone) * 100}%`,
                      background: `rgba(16,185,129,${(0.5 - z.rank * 0.08).toFixed(2)})`,
                    }}
                  />
                </div>
                <span className="num w-20 shrink-0 text-right text-[11px] text-emerald-400">
                  {fmtIDR(z.marginPerM2)}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* 品类毛利 Top8 */}
        <section className="rounded-lg border ds-hairline bg-slate-900/60 p-3.5">
          <h3 className="mb-3 text-xs font-medium text-slate-400">品类毛利 Top 8（日毛利）</h3>
          <div className="space-y-2">
            {cats.map((c) => (
              <div key={c.category} className="flex items-center gap-2">
                <span className="w-32 shrink-0 truncate text-[11px] text-slate-300">{c.category}</span>
                <div className="h-4 flex-1 overflow-hidden rounded-sm bg-slate-800">
                  <div
                    className="h-full rounded-sm bg-emerald-500/70"
                    style={{ width: `${(c.dailyMargin / maxCat) * 100}%` }}
                  />
                </div>
                <span className="num w-20 shrink-0 text-right text-[11px] text-slate-200">
                  {fmtIDR(c.dailyMargin)}
                </span>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="mt-3 grid gap-3 lg:grid-cols-4">
        {/* what-if 前三挪位 */}
        {biz.whatIf.map((w, i) => (
          <div key={w.facing_id} className="rounded-lg border ds-hairline bg-slate-900/60 p-3.5">
            <p className="text-[10px] uppercase tracking-wide text-slate-500">挪位增收 #{i + 1} · {w.zone}</p>
            <p className="mt-1.5 truncate text-xs text-slate-200">{w.to_sku_name}</p>
            <p className="text-[11px] text-slate-500">
              {w.from_sku} → {w.to_sku}
            </p>
            <p className="num mt-2 text-base font-semibold text-emerald-400">
              +{fmtIDR(w.delta_daily_margin_idr)}/hari
            </p>
          </div>
        ))}
        {/* 一键优化总卡 */}
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-3.5">
          <p className="text-[10px] uppercase tracking-wide text-emerald-500/80">全店一键优化（贪心 MILP）</p>
          <p className="num mt-1.5 text-base font-semibold text-emerald-300">
            {preview.count} 个面位 · +{fmtIDR(preview.totalDelta)}/hari
          </p>
          <p className="mt-1 text-[11px] text-slate-500">
            验证重算增量：+{fmtIDR(Math.max(verifiedDelta, 0))}/hari（重算含热力加权，可能略高于贪心目标值）
          </p>
        </div>
        {/* 实时流水 */}
        <div className="rounded-lg border ds-hairline bg-slate-900/60 p-3.5">
          <p className="flex items-center gap-1.5 text-[10px] uppercase tracking-wide text-slate-500">
            实时流水（模拟 POS）
            <span className="h-1 w-1 animate-pulse rounded-full bg-emerald-400" />
          </p>
          <div className="mt-2 space-y-1.5">
            {sim.log.length === 0 && <p className="text-[11px] text-slate-600">等待首笔成交…</p>}
            {sim.log.map((tx) => (
              <div key={tx.id} className="flex items-baseline gap-2 text-[11px]">
                <span className="num shrink-0 text-slate-600">{tx.time}</span>
                <span className="min-w-0 flex-1 truncate text-slate-300">
                  {tx.skuName} <span className="text-slate-500">×{tx.qty}</span>
                </span>
                <span className="num shrink-0 text-emerald-400">+{fmtIDR(tx.margin)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-3 flex items-center gap-3 rounded-lg border border-amber-500/30 bg-amber-500/5 px-3.5 py-2.5">
        <span className="text-amber-400">⚠</span>
        <p className="text-xs text-amber-200/90">
          {biz.bottomFacingIds.size} 个面位处于品类内效率末位 10% —— 建议在 2D 沙盘点击货架替换 SKU，或直接点上方「一键智能优化」。
        </p>
      </div>
    </div>
  )
}
