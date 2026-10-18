import { useMemo, useState } from 'react'
import type { FacingEdit, SeedDoc } from '@/types/seed'
import { computeBiz, fmtIDR, optimizePlan, type BizLayer } from '@/lib/biz'
import { toast } from 'sonner'

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

  const kpis: { label: string; value: string; accent?: string }[] = [
    { label: '总日毛利（全店面位）', value: `${fmtIDR(biz.totalDailyMargin)}/hari`, accent: 'text-emerald-400' },
    { label: '在售 SKU', value: String(new Set(doc.facings.map((f) => f.sku_code)).size - 1) },
    { label: '面位数', value: String(doc.facings.length) },
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
          <h2 className="text-sm font-semibold tracking-wide">经营数据大屏</h2>
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
            <p className="text-[10px] uppercase tracking-wide text-slate-500">{k.label}</p>
            <p className={`num mt-1 text-lg font-semibold ${k.accent ?? 'text-slate-100'}`}>{k.value}</p>
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

      <div className="mt-3 grid gap-3 lg:grid-cols-3">
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
      </div>

      {/* 末位警示条 */}
      <div className="mt-3 flex items-center gap-3 rounded-lg border border-amber-500/30 bg-amber-500/5 px-3.5 py-2.5">
        <span className="text-amber-400">⚠</span>
        <p className="text-xs text-amber-200/90">
          {biz.bottomFacingIds.size} 个面位处于品类内效率末位 10% —— 建议在 2D 沙盘点击货架替换 SKU，或直接点上方「一键智能优化」。
        </p>
      </div>
    </div>
  )
}
