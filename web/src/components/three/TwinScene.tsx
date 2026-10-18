import { Suspense, useMemo } from 'react'
import { Canvas } from '@react-three/fiber'
import { Grid, OrbitControls } from '@react-three/drei'
import type { SeedDoc } from '@/types/seed'
import type { BizLayer } from '@/lib/biz'
import { StoreMesh } from './StoreMesh'

interface TwinSceneProps {
  doc: SeedDoc
  biz: BizLayer
  selectedFixtureId: string | null
  onSelectFixture: (id: string | null) => void
  autoRotate: boolean
}

export function TwinScene({ doc, biz, selectedFixtureId, onSelectFixture, autoRotate }: TwinSceneProps) {
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
