import type { SVGProps } from 'react'

/**
 * NRT 线框图标库 —— Kimi 图标风格移植（极简线性、1.8px 描边、24×24 网格、currentColor）。
 * 用法：<BoxIcon className="h-4 w-4" />，尺寸跟随上下文。
 */

type IconProps = SVGProps<SVGSVGElement>

function base(props: IconProps): IconProps {
  return {
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.8,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    'aria-hidden': true,
    ...props,
  }
}

export function StoreIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M4 9.5 5.4 4.8A1.2 1.2 0 0 1 6.6 4h10.8a1.2 1.2 0 0 1 1.2.8L20 9.5" />
      <path d="M4 9.5v9.7h16V9.5" />
      <path d="M4 9.5c0 1.3 1 2.3 2.3 2.3 1.2 0 2.2-.9 2.3-2.1.1 1.2 1.1 2.1 2.4 2.1s2.3-.9 2.4-2.1c.1 1.2 1.1 2.1 2.3 2.1 1.3 0 2.3-1 2.3-2.3" />
      <path d="M9.5 19.2v-5.2h5v5.2" />
    </svg>
  )
}

export function BoxIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M12 3.2 20 7.6v8.8l-8 4.4-8-4.4V7.6l8-4.4Z" />
      <path d="M4 7.6l8 4.4 8-4.4" />
      <path d="M12 12v8.8" />
    </svg>
  )
}

export function GridIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <rect x="4" y="4" width="16" height="16" rx="1.5" />
      <path d="M4 9.3h16M4 14.6h16M9.3 4v16M14.6 4v16" />
    </svg>
  )
}

export function LeafIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M5 19c0-7.5 5.5-13 14-13 0 8.5-5.5 14-13 14-1 0-1-.5-1-1Z" />
      <path d="M5 19c3-5.5 7-9.5 11-11.5" />
    </svg>
  )
}

export function BadgeCheckIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M12 3.5 14 5.4l2.6-.3.4 2.6 2.3 1.2-1.1 2.3 1.1 2.3-2.3 1.2-.4 2.6-2.6-.3L12 20.5l-2-1.9-2.6.3-.4-2.6-2.3-1.2L4 13l-1.1-2.3L5.2 9.5l.4-2.6 2.6.3L12 3.5Z" />
      <path d="m9.2 12 2 2 3.8-4" />
    </svg>
  )
}

export function CalendarIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <rect x="4" y="5.2" width="16" height="14.8" rx="1.5" />
      <path d="M4 9.8h16M8.2 3.2v3.4M15.8 3.2v3.4" />
    </svg>
  )
}

export function MapIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="m9 4.5-5 1.7v13.3l5-1.7 6 1.7 5-1.7V4.5l-5 1.7-6-1.7Z" />
      <path d="M9 4.5v13.3M15 6.2v13.3" />
    </svg>
  )
}

export function CubeIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="m12 3.5 8 4.4v8.2l-8 4.4-8-4.4V7.9l8-4.4Z" />
      <path d="M4 7.9l8 4.4 8-4.4M12 12.3v8.2" />
    </svg>
  )
}

export function RotateIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M20 12a8 8 0 1 1-2.3-5.6" />
      <path d="M20 3.8v4.4h-4.4" />
    </svg>
  )
}

export function DownloadIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M12 4v10.5M7.5 11 12 15.5 16.5 11" />
      <path d="M4.5 16.5V19a1.5 1.5 0 0 0 1.5 1.5h12A1.5 1.5 0 0 0 19.5 19v-2.5" />
    </svg>
  )
}

export function ResetIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M4.5 8A8 8 0 1 1 4 13.5" />
      <path d="M4.5 3.8v4.4H8.9" />
    </svg>
  )
}

export function EyeIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M2.5 12S6 5.8 12 5.8 21.5 12 21.5 12 18 18.2 12 18.2 2.5 12 2.5 12Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}

export function SearchIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <circle cx="11" cy="11" r="6.5" />
      <path d="m16 16 4.5 4.5" />
    </svg>
  )
}

export function ChartIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M4 20V10M10 20V4M16 20v-8M21 20H3" />
    </svg>
  )
}

export const ICON = {
  store: StoreIcon,
  box: BoxIcon,
  grid: GridIcon,
  leaf: LeafIcon,
  badgeCheck: BadgeCheckIcon,
  calendar: CalendarIcon,
  map: MapIcon,
  cube: CubeIcon,
  rotate: RotateIcon,
  download: DownloadIcon,
  reset: ResetIcon,
  eye: EyeIcon,
  search: SearchIcon,
}
