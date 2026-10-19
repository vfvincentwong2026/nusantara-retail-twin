import { Suspense, useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Grid, Html, OrbitControls } from '@react-three/drei'
import * as THREE from 'three'
import type { SeedDoc, Zone } from '@/types/seed'
import { fmtIDR, type BizLayer } from '@/lib/biz'
import type { Tx } from '@/lib/liveSim'
import { StoreMesh } from './StoreMesh'

interface TwinSceneProps {
  doc: SeedDoc
  biz: BizLayer
  selectedFixtureId: string | null
  onSelectFixture: (id: string | null) => void
  autoRotate: boolean
  /** 实时成交流水（与大屏/2D 共享模拟）：成交分区亮脉冲 */
  lastTx?: Tx | null
}

/** 分区成交脉冲：扩散环 + 金额浮标，1.8s 生命周期（与 2D 脉冲同节奏） */
function ZonePulse({ zone, margin, span }: { zone: Zone; margin: number; span: number }) {
  const ring = useRef<THREE.Mesh>(null)
  const mat = useRef<THREE.MeshBasicMaterial>(null)
  const start = useRef(performance.now())
  const cx = zone.polygon.reduce((s, p) => s + p.x, 0) / zone.polygon.length
  const cz = zone.polygon.reduce((s, p) => s + p.y, 0) / zone.polygon.length
  const base = span / 13
  useFrame(() => {
    const t = (performance.now() - start.current) / 1800
    const s = 0.35 + t * 2.9
    ring.current?.scale.set(s, s, s)
    if (mat.current) mat.current.opacity = Math.max(0, 0.9 * (1 - t))
  })
  return (
    <group position={[cx, 2.6, cz]}>
      <mesh ref={ring} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[base * 0.82, base, 48]} />
        <meshBasicMaterial
          ref={mat}
          color="#6ee7b7"
          transparent
          opacity={0.9}
          side={THREE.DoubleSide}
          depthWrite={false}
        />
      </mesh>
      <Html center position={[0, 1.4, 0]} distanceFactor={span / 7} style={{ pointerEvents: 'none' }}>
        <div className="num whitespace-nowrap rounded border border-emerald-500/50 bg-emerald-950/85 px-1.5 py-0.5 text-xs font-bold text-emerald-300">
          +{fmtIDR(margin)}
        </div>
      </Html>
    </group>
  )
}

export function TwinScene({ doc, biz, selectedFixtureId, onSelectFixture, autoRotate, lastTx }: TwinSceneProps) {
  const center = useMemo(() => {
    const xs = doc.zones.flatMap((z) => z.polygon.map((p) => p.x))
    const ys = doc.zones.flatMap((z) => z.polygon.map((p) => p.y))
    const cx = (Math.min(...xs) + Math.max(...xs)) / 2
    const cz = (Math.min(...ys) + Math.max(...ys)) / 2
    const span = Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys))
    return { cx, cz, span }
  }, [doc])

  return (
    <div className="relative h-full w-full overflow-hidden rounded-lg border bg-slate-950">
      <Canvas
        shadows
        camera={{ position: [center.cx + center.span * 0.7, center.span * 0.9, center.cz + center.span * 0.9], fov: 45, near: 0.1, far: 500 }}
        onPointerMissed={() => onSelectFixture(null)}
      >
        <color attach="background" args={['#020617']} />
        <fog attach="fog" args={['#020617', center.span * 1.2, center.span * 3]} />
        <ambientLight intensity={0.6} />
        <directionalLight
          position={[center.cx + 30, 45, center.cz + 20]}
          intensity={1.15}
          castShadow
          shadow-mapSize={[2048, 2048]}
        />
        <hemisphereLight args={['#64748b', '#0f172a', 0.45]} />
        {/* 沙盘地面网格：低透明细线，科技感衬底 */}
        <Grid
          position={[center.cx, -0.02, center.cz]}
          args={[center.span * 4, center.span * 4]}
          cellSize={1}
          cellThickness={0.6}
          cellColor="#1e293b"
          sectionSize={5}
          sectionThickness={1}
          sectionColor="#334155"
          fadeDistance={center.span * 3.2}
          fadeStrength={2}
        />
        <Suspense fallback={null}>
          <StoreMesh
            doc={doc}
            biz={biz}
            selectedFixtureId={selectedFixtureId}
            onSelectFixture={onSelectFixture}
            autoRotate={autoRotate}
          />
        </Suspense>
        {lastTx &&
          doc.zones
            .filter((z) => z.zone_name === lastTx.zoneName)
            .map((z) => (
              <ZonePulse key={lastTx.id} zone={z} margin={lastTx.margin} span={center.span} />
            ))}
        <OrbitControls
          target={[center.cx, 0, center.cz]}
          maxPolarAngle={Math.PI / 2.05}
          minDistance={3}
          maxDistance={center.span * 3}
          enableDamping
        />
      </Canvas>
      <div className="pointer-events-none absolute left-3 top-3 text-[11px] text-slate-500">
        左键旋转 · 右键平移 · 滚轮缩放 · 点击货架联动 2D 视图
      </div>
    </div>
  )
}
