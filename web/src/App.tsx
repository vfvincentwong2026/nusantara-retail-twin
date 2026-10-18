import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from 'react'
import type { FacingEdit, SeedDoc } from '@/types/seed'
import { downloadJSON, heatColor } from '@/lib/seed'
import { loadSeed, STORE_SIZES } from '@/lib/seed'
import { TopBar } from '@/components/TopBar'
import { Floorplan } from '@/components/Floorplan'
import { Inspector } from '@/components/Inspector'
import { MapIcon, CubeIcon, RotateIcon } from '@/components/ui/icons'
import { Toaster, toast } from 'sonner'

// 3D 视图按需加载（three.js 约 1MB，独立分包）
const TwinScene = lazy(() =>
  import('@/components/three/TwinScene').then((m) => ({ default: m.TwinScene })),
)

type ViewMode = '2d' | '3d'

export default function App() {
  const [size, setSize] = useState<number>(STORE_SIZES[1])
  const [view, setView] = useState<ViewMode>(() =>
    new URLSearchParams(window.location.search).get('view') === '3d' ? '3d' : '2d',
  )
  const [autoRotate, setAutoRotate] = useState(false)
  const [doc, setDoc] = useState<SeedDoc | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedFixtureId, setSelectedFixtureId] = useState<string | null>(null)
  const [edits, setEdits] = useState<Record<string, FacingEdit>>({})

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    setSelectedFixtureId(null)
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

  const onResetEdits = useCallback(() => setEdits({}), [])

  const onExport = useCallback(() => {
    if (!doc) return
    const facings = doc.facings.map((fc) => {
      const e = edits[fc.facing_id]
      return e ? { ...fc, sku_code: e.sku_code, max_units: e.max_units } : fc
    })
    const out = { ...doc, facings }
    downloadJSON(out, `store_${size}sqm_edited.json`)
    toast.success(`已导出 ${Object.keys(edits).length} 处修改`)
  }, [doc, edits, size])

  const dirtyCount = Object.keys(edits).length
  const heatLegend = useMemo(() => [0, 0.25, 0.5, 0.75, 1], [])

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
        <main className="min-w-0 flex-1">
          {doc ? (
            view === '2d' ? (
              <Floorplan doc={doc} selectedFixtureId={selectedFixtureId} onSelectFixture={setSelectedFixtureId} />
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
                  selectedFixtureId={selectedFixtureId}
                  onSelectFixture={setSelectedFixtureId}
                  autoRotate={autoRotate}
                />
              </Suspense>
            )
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
              {error ? '种子数据加载失败' : '加载种子数据…'}
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
        <aside className="w-[420px] shrink-0">
          {doc && (
            <Inspector
              doc={doc}
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
