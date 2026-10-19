import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { FacingEdit, FixtureEdit, SeedDoc } from '@/types/seed'
import { downloadJSON, heatColor } from '@/lib/seed'
import { computeBiz, facingDelta, fmtIDR, optimizePlan, type BizLayer } from '@/lib/biz'
import { useLiveSim } from '@/lib/liveSim'
import { loadSeed, STORE_SIZES } from '@/lib/seed'
import { TopBar } from '@/components/TopBar'
import { Floorplan } from '@/components/Floorplan'
import { Inspector } from '@/components/Inspector'
import { Dashboard } from '@/components/Dashboard'
import { MapIcon, CubeIcon, RotateIcon, ChartIcon } from '@/components/ui/icons'
import { Toaster, toast } from 'sonner'

// 3D 视图按需加载（three.js 约 1MB，独立分包）
const TwinScene = lazy(() =>
  import('@/components/three/TwinScene').then((m) => ({ default: m.TwinScene })),
)

type ViewMode = '2d' | '3d' | 'dash'

const VIEW_FROM_URL = (): ViewMode => {
  const v = new URLSearchParams(window.location.search).get('view')
  return v === '3d' ? '3d' : v === 'dash' ? 'dash' : '2d'
}

export default function App() {
  const [size, setSize] = useState<number>(STORE_SIZES[1])
  const [view, setView] = useState<ViewMode>(VIEW_FROM_URL)
  const [autoRotate, setAutoRotate] = useState(false)
  const [doc, setDoc] = useState<SeedDoc | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedFixtureId, setSelectedFixtureId] = useState<string | null>(null)
  const [edits, setEdits] = useState<Record<string, FacingEdit>>({})
  const [fixtureEdits, setFixtureEdits] = useState<Record<string, FixtureEdit>>({})
  // 智能优化应用/撤销（洽谈时前后对比）
  const [optBackup, setOptBackup] = useState<Record<string, FacingEdit | null> | null>(null)
  const [optApplied, setOptApplied] = useState(false)

  const applyPlan = useCallback(
    (batch: Record<string, FacingEdit>) => {
      const backup: Record<string, FacingEdit | null> = {}
      for (const id of Object.keys(batch)) backup[id] = edits[id] ?? null
      setOptBackup(backup)
      setEdits((prev) => ({ ...prev, ...batch }))
      setOptApplied(true)
    },
    [edits],
  )
  const undoPlan = useCallback(() => {
    setEdits((prev) => {
      const next = { ...prev }
      if (optBackup) {
        for (const [id, e] of Object.entries(optBackup)) {
          if (e === null) delete next[id]
          else next[id] = e
        }
      }
      return next
    })
    setOptBackup(null)
    setOptApplied(false)
  }, [optBackup])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    setSelectedFixtureId(null)
    setOptBackup(null)
    setOptApplied(false)
    loadSeed(size)
      .then((d) => {
        if (cancelled) return
        setDoc(d)
        // 深链：?fixture=F-001 直接定位货架
        const label = new URLSearchParams(window.location.search).get('fixture')
        if (label) {
          const f = d.fixtures.find((fx) => fx.fixture_label === label)
          if (f) setSelectedFixtureId(f.fixture_id)
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [size])

  const onEdit = useCallback((facingId: string, edit: FacingEdit) => {
    setEdits((prev) => ({ ...prev, [facingId]: edit }))
  }, [])

  const onResetEdits = useCallback(() => {
    setEdits({})
    setFixtureEdits({})
  }, [])

  const onMoveFixture = useCallback((id: string, x: number, y: number) => {
    setFixtureEdits((prev) => ({ ...prev, [id]: { position_x: x, position_y: y } }))
    toast.success(`货架已移动至 (${x.toFixed(1)}, ${y.toFixed(1)})m`)
  }, [])

  const onExport = useCallback(() => {
    if (!doc) return
    const facings = doc.facings.map((fc) => {
      const e = edits[fc.facing_id]
      return e ? { ...fc, sku_code: e.sku_code, max_units: e.max_units } : fc
    })
    const fixtures = doc.fixtures.map((f) => ({ ...f, ...fixtureEdits[f.fixture_id] }))
    const out = { ...doc, facings, fixtures }
    const n = Object.keys(edits).length + Object.keys(fixtureEdits).length
    downloadJSON(out, `store_${size}sqm_edited.json`)
    toast.success(`已导出 ${n} 处修改`)
  }, [doc, edits, fixtureEdits, size])

  const dirtyCount = Object.keys(edits).length + Object.keys(fixtureEdits).length
  const marginDelta = useMemo(() => {
    if (!doc) return 0
    let d = 0
    for (const [facingId, e] of Object.entries(edits)) {
      if (e.sku_code) d += facingDelta(doc, facingId, e.sku_code)
    }
    return d
  }, [doc, edits])
  const heatLegend = useMemo(() => [0, 0.25, 0.5, 0.75, 1], [])
  const biz: BizLayer | null = useMemo(() => (doc ? computeBiz(doc) : null), [doc])
  // 实时经营模拟提升到 App 层：大屏显示流水，2D 平面图同步分区脉冲
  const sim = useLiveSim(doc)
  // 演示模式：?demo=1 —— 洽谈第一屏；?demo=1 且带 auto=1 时自动轮播三视图 + 自动优化
  const demoMode = useMemo(() => new URLSearchParams(window.location.search).get('demo') === '1', [])
  const demoAuto = useMemo(() => demoMode && new URLSearchParams(window.location.search).get('auto') === '1', [demoMode])
  const DEMO_ORDER: ViewMode[] = ['2d', '3d', 'dash']
  const demoOptDone = useRef(false)
  const applyPlanRef = useRef(applyPlan)
  applyPlanRef.current = applyPlan
  // 自动轮播：2D → 3D → 大屏，每 8s 一步；轮播到大屏 2.5s 后自动执行智能优化（避开 React effect 清理）
  useEffect(() => {
    if (!demoAuto || !doc) return
    let step = 0
    setView(DEMO_ORDER[0])
    const t = setInterval(() => {
      step += 1
      const v = DEMO_ORDER[step % DEMO_ORDER.length]
      setView(v)
      if (v === 'dash' && !demoOptDone.current) {
        demoOptDone.current = true
        setTimeout(() => {
          const { plan, totalDelta } = optimizePlan(doc)
          const batch: Record<string, FacingEdit> = {}
          for (const [fid, s] of Object.entries(plan)) {
            const fc = doc.facings.find((f) => f.facing_id === fid)
            batch[fid] = { sku_code: s.sku_code, max_units: fc?.max_units ?? 1 }
          }
          if (Object.keys(batch).length) {
            applyPlanRef.current(batch)
            toast.success(`演示 · 一键智能优化：+${fmtIDR(totalDelta)}/hari`)
          }
        }, 2500)
      }
    }, 8000)
    return () => clearInterval(t)
  }, [demoAuto, doc])

  return (
    <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
      <div className="border-b border-slate-800 px-4 py-3">
        <TopBar doc={doc} size={size} loading={loading} error={error} onSwitchSize={setSize} />
        <div className="mt-2.5 flex items-center gap-3">
          <div className="flex rounded-lg border ds-hairline p-0.5">
            {(
              [
                { v: '2d', label: '2D 平面图', Icon: MapIcon },
                { v: '3d', label: '3D 数字孪生', Icon: CubeIcon },
                { v: 'dash', label: '经营大屏', Icon: ChartIcon },
              ] as const
            ).map(({ v, label, Icon }) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                  v === view
                    ? 'bg-foreground text-background'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
              </button>
            ))}
          </div>
          {view === '3d' && (
            <label className="flex cursor-pointer items-center gap-2 text-xs text-muted-foreground transition-colors hover:text-foreground">
              <input
                type="checkbox"
                checked={autoRotate}
                onChange={(e) => setAutoRotate(e.target.checked)}
                className="h-3.5 w-3.5 rounded accent-current"
              />
              <RotateIcon className="h-3.5 w-3.5 opacity-70" />
              自动旋转
            </label>
          )}
        </div>
      </div>
      <div className="flex min-h-0 flex-1 gap-3 p-3">
        <main className="relative min-w-0 flex-1">
          {doc && biz && demoMode && view !== 'dash' && (
            <div className="pointer-events-none absolute right-4 top-4 z-10 w-72 space-y-2">
              <div className="rounded-lg border ds-hairline bg-slate-900/85 px-3.5 py-3 backdrop-blur">
                <p className="text-[11px] text-slate-400">总日毛利（全店面位合计）</p>
                <p className="num text-lg font-medium text-emerald-400">{fmtIDR(biz.totalDailyMargin)}/hari</p>
              </div>
              {biz.whatIf.map((w) => (
                <div key={w.facing_id} className="rounded-lg border ds-hairline bg-slate-900/85 px-3.5 py-2.5 backdrop-blur">
                  <p className="text-xs text-slate-200">挪位增收 #{biz.whatIf.indexOf(w) + 1}</p>
                  <p className="truncate text-[11px] text-slate-400">{w.to_sku_name}</p>
                  <p className="num text-sm font-medium text-emerald-400">
                    +{fmtIDR(w.delta_daily_margin_idr)}/hari
                  </p>
                </div>
              ))}
            </div>
          )}
          {doc && biz && demoMode && (
            <div className="pointer-events-none absolute bottom-3 left-1/2 z-10 -translate-x-1/2 rounded-full border ds-hairline bg-slate-900/85 px-4 py-1.5 text-xs text-slate-200 backdrop-blur">
              {view === '2d' && '① 空间价值可视化 —— 颜色越亮，每平米越赚钱'}
              {view === '3d' && '② 数字孪生 —— 货架 1:1 还原，可旋转查看每层陈列'}
              {view === 'dash' &&
                (optApplied
                  ? '③ 智能优化已生效 —— 看底部日毛利增量，点撤销可对比'
                  : '③ 经营大屏 —— 实时流水 · 品类毛利 · 一键智能优化')}
            </div>
          )}
          {doc && biz ? (
            view === '2d' ? (
              <Floorplan doc={doc} biz={biz} fixtureEdits={fixtureEdits} selectedFixtureId={selectedFixtureId} onSelectFixture={setSelectedFixtureId} onMoveFixture={onMoveFixture} lastTx={sim.log[0] ?? null} />
            ) : view === 'dash' ? (
              <Dashboard
                doc={doc}
                biz={biz}
                sim={sim}
                optimized={optApplied}
                onApplyPlan={applyPlan}
                onUndoPlan={undoPlan}
              />
            ) : (
              <Suspense
                fallback={
                  <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                    加载 3D 引擎…
                  </div>
                }
              >
                <TwinScene
                  doc={doc}
                  biz={biz}
                  selectedFixtureId={selectedFixtureId}
                  onSelectFixture={setSelectedFixtureId}
                  autoRotate={autoRotate}
                  lastTx={sim.log[0] ?? null}
                />
              </Suspense>
            )
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
              {error ? '种子数据加载失败' : '加载种子数据…'}
            </div>
          )}
          {dirtyCount > 0 && (
            <div className="mt-2 flex items-center gap-3 rounded-lg border ds-hairline bg-slate-900/70 px-3 py-1.5 text-xs backdrop-blur">
              <span className="text-muted-foreground">本次调整对全店日毛利影响</span>
              <span className={`num font-medium ${marginDelta >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {marginDelta >= 0 ? '+' : ''}{fmtIDR(marginDelta)}/hari
              </span>
              <span className="text-slate-600">（含 {Object.keys(fixtureEdits).length} 处货架移动 + {Object.keys(edits).length} 处面位调整）</span>
            </div>
          )}
          {/* 图例 */}
          <div className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-1 px-1 text-[11px] text-muted-foreground">
            <span className="flex items-center gap-1.5">
              去化热力
              {heatLegend.map((h) => (
                <span key={h} className="inline-block h-3 w-3 rounded-sm" style={{ background: heatColor(h) }} />
              ))}
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-sm bg-slate-400" /> 中岛货架
              <span className="inline-block h-3 w-3 rounded-sm bg-sky-400" /> 冷柜
              <span className="inline-block h-3 w-3 rounded-sm bg-indigo-400" /> 冷冻柜
            </span>
            {view === '3d' && <span className="text-slate-600">面位色块 = 商品品类（与 2D 编辑器一致）</span>}
          </div>
        </main>
        <aside className={`w-[420px] shrink-0 ${demoMode || view === 'dash' ? 'hidden' : ''}`}>
          {doc && biz && (
            <Inspector
              doc={doc}
              biz={biz}
              fixtureId={selectedFixtureId}
              edits={edits}
              onEdit={onEdit}
              onResetEdits={onResetEdits}
              onExport={onExport}
              dirtyCount={dirtyCount}
            />
          )}
        </aside>
      </div>
      <Toaster theme="dark" position="bottom-right" />
    </div>
  )
}
