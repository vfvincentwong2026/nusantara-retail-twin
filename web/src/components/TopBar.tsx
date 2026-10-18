import type { ReactNode } from 'react'
import type { SeedDoc } from '@/types/seed'
import { STORE_SIZES } from '@/lib/seed'
import { Badge } from '@/components/ui/badge'
import { StoreIcon, BoxIcon, GridIcon, LeafIcon, BadgeCheckIcon, CalendarIcon } from '@/components/ui/icons'

interface TopBarProps {
  doc: SeedDoc | null
  size: number
  loading: boolean
  error: string | null
  onSwitchSize: (size: number) => void
}

function MetaItem({ icon: Icon, children }: { icon: typeof BoxIcon; children: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-muted-foreground">
      <Icon className="h-3.5 w-3.5 opacity-70" />
      <span className="num">{children}</span>
    </span>
  )
}

export function TopBar({ doc, size, loading, error, onSwitchSize }: TopBarProps) {
  const p = doc?.store_profile
  const gs = doc?.generation_summary
  return (
    <header className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg border ds-hairline text-foreground">
            <StoreIcon className="h-[18px] w-[18px]" />
          </span>
          <div>
            <h1 className="text-[17px] font-medium leading-tight">Nusantara Retail Twin</h1>
            <p className="text-xs text-muted-foreground">零售空间数字孪生 · 2D 平面图编辑器</p>
          </div>
        </div>
        <div className="flex rounded-lg border ds-hairline p-0.5">
          {STORE_SIZES.map((s) => (
            <button
              key={s}
              onClick={() => onSwitchSize(s)}
              className={`num rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                s === size
                  ? 'bg-foreground text-background'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              }`}
            >
              {s}㎡
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs text-destructive">
          {error}
        </div>
      )}

      {doc && p && gs && (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs">
          <span className="font-medium">{p.store_name}</span>
          <Badge variant="secondary">{p.store_format}</Badge>
          <MetaItem icon={BoxIcon}>SKU {gs.skus_count.toLocaleString()}</MetaItem>
          <MetaItem icon={GridIcon}>Facings {gs.facings_count.toLocaleString()}</MetaItem>
          <MetaItem icon={LeafIcon}>生鲜 {((gs.fresh_skus_count / gs.skus_count) * 100).toFixed(0)}%</MetaItem>
          <MetaItem icon={BadgeCheckIcon}>清真 {((gs.halal_certified_skus_count / gs.skus_count) * 100).toFixed(0)}%</MetaItem>
          <MetaItem icon={CalendarIcon}>
            斋月 {doc.ramadan_calendar_2026.ramadan_start} → 开斋节 {doc.ramadan_calendar_2026.lebaran_date}
          </MetaItem>
          {loading && (
            <span className="inline-flex items-center gap-1.5 text-muted-foreground">
              <span className="h-3 w-3 animate-spin rounded-full border border-muted-foreground/30 border-t-muted-foreground" />
              加载中
            </span>
          )}
        </div>
      )}
    </header>
  )
}
