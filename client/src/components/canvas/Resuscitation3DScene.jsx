import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { AnatomicalRescueModel } from './AnatomicalRescueModel';

/**
 * Resuscitation3DScene
 * High-fidelity 3D WebGL anatomical cross-sectional resuscitation visualization.
 * Matches clinical Pinterest reference (https://pin.it/xAC3cOf1M):
 * - Dark medical visualization background (#080C14)
 * - Supine real human body with translucent X-ray diagnostic contour
 * - Cross-sectional brain, cervical spine, heart, ribs, carotid arteries, jugular veins
 * - Dynamic cerebral blood perfusion waves surging on each 110 BPM compression stroke
 * - Compressing rescuer hands on sternum
 */
export function Resuscitation3DScene({ isCPRActive = false, beatPhase = 0 }) {
  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: '240px',
        borderRadius: '8px',
        overflow: 'hidden',
        background: 'radial-gradient(circle at 45% 50%, #111827 0%, #080C14 85%)',
        border: '1px solid rgba(56, 189, 248, 0.15)',
        boxShadow: 'inset 0 0 25px rgba(0, 0, 0, 0.6)',
      }}
    >
      <Canvas
        camera={{ position: [0, 0.08, 0.85], fov: 38 }}
        style={{ width: '100%', height: '100%' }}
      >
        <Suspense fallback={null}>
          {/* Clinical Diagnostic Studio Lighting */}
          <ambientLight intensity={0.9} />
          
          {/* Top Surgical Focus Spot onto Sternum & Compressions */}
          <directionalLight position={[0.2, 2.5, 1.5]} intensity={2.6} color="#FFFFFF" />

          {/* Cyan Back / Rim Light: highlights translucent human facial & chest silhouette */}
          <directionalLight position={[-1.8, 0.8, -1.2]} intensity={2.8} color="#38BDF8" />
          <directionalLight position={[1.5, -0.8, -1.0]} intensity={1.4} color="#0284C7" />

          {/* Front Fill Light */}
          <directionalLight position={[0, 0.5, 2.0]} intensity={1.2} color="#E2E8F0" />

          {/* Pulsing Arterial Blood / Cardiac Glow */}
          <pointLight
            position={[-0.1, 0.02, 0.15]}
            intensity={isCPRActive ? 3.5 : 1.2}
            color={isCPRActive ? '#EF4444' : '#F59E0B'}
            distance={1.6}
          />

          {/* 3D Anatomical Human Resuscitation Model with Internal Perfusion */}
          <AnatomicalRescueModel isCPRActive={isCPRActive} beatPhase={beatPhase} />
        </Suspense>

        {/* Smooth 360° Medical Orbit Controls */}
        <OrbitControls
          enableZoom={true}
          maxDistance={1.4}
          minDistance={0.45}
          enablePan={false}
          maxPolarAngle={Math.PI / 1.7}
          minPolarAngle={Math.PI / 5}
          rotateSpeed={0.7}
        />
      </Canvas>

      {/* Medical Telemetry Overlay Badge */}
      <div
        style={{
          position: 'absolute',
          top: '8px',
          left: '10px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '3px 8px',
          background: 'rgba(15, 23, 42, 0.82)',
          backdropFilter: 'blur(6px)',
          borderRadius: '4px',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          fontSize: '9px',
          fontFamily: 'var(--font-mono)',
          fontWeight: 700,
          color: isCPRActive ? '#38BDF8' : '#94A3B8',
          letterSpacing: '0.5px',
          pointerEvents: 'none',
        }}
      >
        <span
          style={{
            display: 'inline-block',
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: isCPRActive ? '#22C55E' : '#F59E0B',
            boxShadow: isCPRActive ? '0 0 6px #22C55E' : 'none',
          }}
        />
        {isCPRActive ? 'CEREBRAL BLOOD FLOW: 100%' : 'ANATOMICAL CROSS-SECTION (SUPINE)'}
      </div>

      {/* Interactive Drag & Rotate Prompt */}
      <div
        style={{
          position: 'absolute',
          bottom: '6px',
          left: '10px',
          right: '10px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          pointerEvents: 'none',
          fontSize: '9px',
          fontFamily: 'var(--font-mono)',
          color: '#64748B',
          fontWeight: 700,
        }}
      >
        <span style={{ color: isCPRActive ? '#EF4444' : '#00A8E8' }}>
          {isCPRActive ? '● CAROTID-CEREBRAL PERFUSION ACTIVE (110 BPM)' : '● 3D HUMAN ANATOMICAL MODEL'}
        </span>
        <span style={{ color: '#94A3B8' }}>DRAG TO ROTATE 3D</span>
      </div>
    </div>
  );
}
