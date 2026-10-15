import type { SeedDoc } from '@/types/seed'
import { STORE_SIZES } from '@/lib/seed'
import { Badge } from '@/components/ui/badge'

interface TopBarProps {
  doc: SeedDoc | null
  size: number
  loading: boolean
  error: string | null
  onSwitchSize: (size: number) => void
}

export function TopBar({ doc, size, loading, error, onSwitchSize }: TopBarProps) {
  const p = doc?.store_profile
  const gs = doc?.generation_summary
  return (
    <header className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold leading-tight">Nusantara Retail Twin</h1>
          <p className="text-xs text-muted-foreground">
            零售空间数字孪生 · 2D 平面图编辑器（Phase 2）
          </p>
        </div>
        <div className="flex rounded-lg border p-0.5">
          {STORE_SIZES.map((s) => (
            <button
              key={s}
              onClick={() => onSwitchSize(s)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                s === size ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-slate-800'
              }`}
            >
              {s}㎡
            </button>
          ))}
        </div>
      </div>

      {error && <div className="rounded-md border border-red-800 bg-red-950/60 px-3 py-2 text-xs text-red-200">{error}</div>}

      {doc && p && gs && (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
          <span className="font-medium text-foreground">{p.store_name}</span>
          <Badge variant="secondary">{p.store_format}</Badge>
          <span>SKU {gs.skus_count.toLocaleString()}</span>
          <span>Facings {gs.facings_count.toLocaleString()}</span>
          <span>生鲜 {((gs.fresh_skus_count / gs.skus_count) * 100).toFixed(0)}%</span>
          <span>清真 {((gs.halal_certified_skus_count / gs.skus_count) * 100).toFixed(0)}%</span>
          <span>斋月 {doc.ramadan_calendar_2026.ramadan_start} → 开斋节 {doc.ramadan_calendar_2026.lebaran_date}</span>
          {loading && <span className="text-amber-400">加载中…</span>}
        </div>
      )}
    </header>
  )
}
