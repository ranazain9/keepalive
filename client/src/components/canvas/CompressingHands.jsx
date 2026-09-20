import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';

/**
 * CompressingHands
 * Realistic 3D human rescuer hands with locked wrists and forearms.
 * Interlocked hand placement positioned exactly over lower half of the sternum.
 * Features real-time downward CPR compressions (2.2 inches / 0.16 units) synced to metronome.
 */
export function CompressingHands({ isCPRActive = false, beatPhase = 0 }) {
  const handsGroupRef = useRef();

  // Lifelike skin tone for rescuer's hands
  const handSkinProps = {
    color: '#DDB29E',
    roughness: 0.5,
    metalness: 0.05,
  };

  useFrame(() => {
    if (!handsGroupRef.current) return;

    if (isCPRActive) {
      // Direct beatPhase compression curve: compress down and into sternum
      const stroke = Math.max(0, Math.sin(beatPhase * Math.PI));
      const displacementZ = stroke * 0.07;
      const displacementY = stroke * 0.03;
      handsGroupRef.current.position.z = 0.22 - displacementZ;
      handsGroupRef.current.position.y = -0.03 - displacementY;
    } else {
      handsGroupRef.current.position.z = 0.22;
      handsGroupRef.current.position.y = -0.03;
    }
  });

  return (
    <group ref={handsGroupRef} position={[0, -0.03, 0.22]} rotation={[-0.15, 0, 0]}>
      {/* ====================================================================
          Lower Hand (Heel of Palm firmly on sternum)
          ==================================================================== */}
      {/* Palm / Heel */}
      <mesh position={[0, 0, 0]} scale={[1.1, 0.35, 1.2]}>
        <sphereGeometry args={[0.18, 24, 24]} />
        <meshStandardMaterial {...handSkinProps} />
      </mesh>

      {/* Lower Hand Fingers (Fanned out over patient's left chest) */}
      {[-0.09, -0.03, 0.03, 0.09].map((xOffset, idx) => (
        <mesh
          key={`l-finger-${idx}`}
          position={[xOffset - 0.14, 0.01, 0.18 + Math.abs(idx - 1.5) * 0.02]}
          rotation={[0.15, -0.2, -0.1]}
        >
          <cylinderGeometry args={[0.022, 0.025, 0.26, 16]} />
          <meshStandardMaterial {...handSkinProps} />
        </mesh>
      ))}

      {/* Lower Hand Thumb */}
      <mesh position={[0.14, 0.02, 0.04]} rotation={[0.3, 0.6, 0.2]}>
        <cylinderGeometry args={[0.026, 0.03, 0.18, 16]} />
        <meshStandardMaterial {...handSkinProps} />
      </mesh>

      {/* ====================================================================
          Upper Hand (Interlaced Fingers gripping lower hand)
          ==================================================================== */}
      {/* Upper Palm */}
      <mesh position={[0.04, 0.09, 0.02]} rotation={[-0.05, -0.15, 0.1]} scale={[1.1, 0.38, 1.2]}>
        <sphereGeometry args={[0.19, 24, 24]} />
        <meshStandardMaterial color="#E2B7A3" roughness={0.48} />
      </mesh>

      {/* Interlaced Upper Fingers */}
      {[-0.08, -0.02, 0.04, 0.1].map((xOffset, idx) => (
        <mesh
          key={`u-finger-${idx}`}
          position={[xOffset - 0.08, 0.08, 0.2]}
          rotation={[0.35, -0.1, -0.05]}
        >
          <cylinderGeometry args={[0.024, 0.026, 0.25, 16]} />
          <meshStandardMaterial color="#E2B7A3" roughness={0.48} />
        </mesh>
      ))}

      {/* ====================================================================
          Rescuer Forearms (Locked Elbows at 90° CPR Angle)
          ==================================================================== */}
      {/* Primary Compressing Forearm */}
      <mesh position={[0.42, 0.52, 0.38]} rotation={[-0.68, 0.28, -0.42]}>
        <cylinderGeometry args={[0.095, 0.08, 1.1, 24]} />
        <meshStandardMaterial {...handSkinProps} />
      </mesh>

      {/* Supporting Forearm */}
      <mesh position={[0.55, 0.56, 0.26]} rotation={[-0.62, 0.35, -0.38]}>
        <cylinderGeometry args={[0.09, 0.075, 1.05, 24]} />
        <meshStandardMaterial {...handSkinProps} />
      </mesh>
    </group>
  );
}
