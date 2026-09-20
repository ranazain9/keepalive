import React from 'react';

/**
 * AnatomicalTorso
 * Realistic 3D anatomical CPR training manikin torso.
 * Accurately modeled with:
 * - Lifelike medical silicone/skin tone (#E5C4B2)
 * - Tilted-back head in resuscitation airway-open sniffing position
 * - Anatomical nose, jawline, neck, and clavicles
 * - Muscular pectoral contours with anatomical sternum depression
 * - Deltoid shoulders and ribs
 */
export function AnatomicalTorso({ isCPRActive = false, beatPhase = 0 }) {
  // Realistic medical manikin skin material
  const skinMaterialProps = {
    color: '#E5C4B2',
    roughness: 0.48,
    metalness: 0.04,
  };

  const chestDepression = isCPRActive ? Math.max(0, Math.sin(beatPhase * Math.PI) * 0.08) : 0;

  return (
    <group position={[0, -0.15, 0.1]}>
      {/* 1. Main Upper Torso / Ribcage (Supine on back) */}
      <mesh position={[0, -chestDepression * 0.5, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.74, 0.65, 1.4, 32]} />
        <meshStandardMaterial {...skinMaterialProps} />
      </mesh>

      {/* 2. Left Pectoral Muscle Contour */}
      <mesh position={[-0.32, 0.22 - chestDepression * 0.7, -0.25]} rotation={[0.2, 0.1, 0.1]}>
        <sphereGeometry args={[0.34, 32, 16]} />
        <meshStandardMaterial {...skinMaterialProps} />
      </mesh>

      {/* 3. Right Pectoral Muscle Contour */}
      <mesh position={[0.32, 0.22 - chestDepression * 0.7, -0.25]} rotation={[0.2, -0.1, -0.1]}>
        <sphereGeometry args={[0.34, 32, 16]} />
        <meshStandardMaterial {...skinMaterialProps} />
      </mesh>

      {/* 4. Left Nipple Landmark (AHA reference for hand placement) */}
      <mesh position={[-0.42, 0.26, -0.12]}>
        <sphereGeometry args={[0.028, 16, 16]} />
        <meshStandardMaterial color="#D09E8C" roughness={0.6} />
      </mesh>

      {/* 5. Right Nipple Landmark */}
      <mesh position={[0.42, 0.26, -0.12]}>
        <sphereGeometry args={[0.028, 16, 16]} />
        <meshStandardMaterial color="#D09E8C" roughness={0.6} />
      </mesh>

      {/* 6. Left Deltoid Shoulder */}
      <mesh position={[-0.92, 0.05, -0.7]}>
        <sphereGeometry args={[0.28, 32, 32]} />
        <meshStandardMaterial {...skinMaterialProps} />
      </mesh>

      {/* 7. Right Deltoid Shoulder */}
      <mesh position={[0.92, 0.05, -0.7]}>
        <sphereGeometry args={[0.28, 32, 32]} />
        <meshStandardMaterial {...skinMaterialProps} />
      </mesh>

      {/* 8. Clavicle / Collarbone Ridge */}
      <mesh position={[0, 0.18, -0.72]} rotation={[0, 0, 0]}>
        <boxGeometry args={[1.3, 0.08, 0.12]} />
        <meshStandardMaterial color="#DBB5A2" roughness={0.5} />
      </mesh>

      {/* 9. Neck (Anatomical tilt toward head) */}
      <mesh position={[0, 0.18, -1.05]} rotation={[0.35, 0, 0]}>
        <cylinderGeometry args={[0.22, 0.26, 0.45, 32]} />
        <meshStandardMaterial {...skinMaterialProps} />
      </mesh>

      {/* 10. Anatomical Head (Tilted back in airway-opening sniffing position) */}
      <group position={[0, 0.32, -1.45]} rotation={[-0.38, 0, 0]}>
        {/* Cranium */}
        <mesh position={[0, 0.08, 0]} scale={[0.88, 1.15, 0.95]}>
          <sphereGeometry args={[0.38, 32, 32]} />
          <meshStandardMaterial {...skinMaterialProps} />
        </mesh>

        {/* Jaw & Chin prominence */}
        <mesh position={[0, -0.16, 0.18]} scale={[0.7, 0.6, 0.8]}>
          <sphereGeometry args={[0.22, 24, 24]} />
          <meshStandardMaterial {...skinMaterialProps} />
        </mesh>

        {/* Anatomical Nose */}
        <mesh position={[0, 0.04, 0.38]} rotation={[0.4, 0, 0]}>
          <coneGeometry args={[0.07, 0.18, 16]} />
          <meshStandardMaterial color="#E2BCAB" roughness={0.45} />
        </mesh>

        {/* Closed Left Eye Orbit */}
        <mesh position={[-0.14, 0.12, 0.32]} rotation={[0.2, -0.2, 0]}>
          <boxGeometry args={[0.1, 0.03, 0.04]} />
          <meshStandardMaterial color="#C89A88" roughness={0.6} />
        </mesh>

        {/* Closed Right Eye Orbit */}
        <mesh position={[0.14, 0.12, 0.32]} rotation={[0.2, 0.2, 0]}>
          <boxGeometry args={[0.1, 0.03, 0.04]} />
          <meshStandardMaterial color="#C89A88" roughness={0.6} />
        </mesh>

        {/* Lips */}
        <mesh position={[0, -0.09, 0.36]}>
          <boxGeometry args={[0.14, 0.04, 0.03]} />
          <meshStandardMaterial color="#D19A8A" roughness={0.5} />
        </mesh>
      </group>

      {/* 11. Lower Abdomen Taper */}
      <mesh position={[0, -0.05, 0.85]} rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.58, 0.68, 0.6, 32]} />
        <meshStandardMaterial {...skinMaterialProps} />
      </mesh>

      {/* 12. Medical Resuscitation Ground Surface Shadow */}
      <mesh position={[0, -0.36, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[5, 5]} />
        <meshBasicMaterial color="#E2E8F0" transparent opacity={0.6} />
      </mesh>
    </group>
  );
}
