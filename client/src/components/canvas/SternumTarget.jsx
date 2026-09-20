import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';

/**
 * SternumTarget
 * 3D illuminated concentric target rings centered over the sternum.
 * Features a glowing yellow core, amber mid-ring, and radiant red outer aura.
 */
export function SternumTarget({ active = false, beatPhase = 0 }) {
  const ringRef = useRef();

  useFrame(() => {
    if (!ringRef.current) return;
    const pulse = active ? 1 + Math.sin(beatPhase * Math.PI) * 0.15 : 1;
    ringRef.current.scale.set(pulse, pulse, 1);
  });

  return (
    <group ref={ringRef} position={[0, -0.03, 0.16]} rotation={[-0.15, 0, 0]}>
      {/* Outer Crimson Aura Ring */}
      <mesh>
        <ringGeometry args={[0.34, 0.38, 36]} />
        <meshBasicMaterial
          color="#EF4444"
          transparent
          opacity={active ? 0.85 : 0.45}
        />
      </mesh>

      {/* Mid Amber Target Ring */}
      <mesh>
        <ringGeometry args={[0.22, 0.26, 36]} />
        <meshBasicMaterial
          color="#F59E0B"
          transparent
          opacity={active ? 0.95 : 0.65}
        />
      </mesh>

      {/* Inner Yellow Core Ring */}
      <mesh>
        <ringGeometry args={[0.12, 0.16, 36]} />
        <meshBasicMaterial
          color="#FBBF24"
          transparent
          opacity={0.95}
        />
      </mesh>

      {/* Center Golden Sternum Dot */}
      <mesh>
        <circleGeometry args={[0.06, 24]} />
        <meshBasicMaterial color="#FBBF24" />
      </mesh>

      {/* Subtle Directional Crosshair Marks */}
      <mesh position={[0, 0, 0.002]}>
        <planeGeometry args={[0.7, 0.015]} />
        <meshBasicMaterial color="#EF4444" transparent opacity={0.5} />
      </mesh>
      <mesh position={[0, 0, 0.002]}>
        <planeGeometry args={[0.015, 0.7]} />
        <meshBasicMaterial color="#EF4444" transparent opacity={0.5} />
      </mesh>
    </group>
  );
}
