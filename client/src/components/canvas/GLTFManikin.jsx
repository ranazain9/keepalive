import React, { useMemo } from 'react';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';

/**
 * GLTFManikin
 * Real 3D Anatomical CPR Resuscitation Manikin.
 * - Rigged humanoid model posed in anatomical CPR training position
 * - Realistic medical manikin silicone flesh tone
 * - Airway-open sniffing position (head and neck tilted back)
 * - Arms rested naturally at sides of torso
 * - Real-time compression displacement synced to 110 BPM metronome
 */
export function GLTFManikin({ isCPRActive = false, beatPhase = 0 }) {
  const { scene } = useGLTF('/models/manikin.glb');

  // Clone scene and pose the skeleton
  const clonedScene = useMemo(() => {
    const clone = scene.clone(true);

    // Realistic medical manikin silicone skin material
    const skinMaterial = new THREE.MeshStandardMaterial({
      color: new THREE.Color('#DFB29D'),
      roughness: 0.44,
      metalness: 0.04,
      flatShading: false,
    });

    clone.traverse((child) => {
      if (child.isMesh) {
        child.material = skinMaterial;
        child.castShadow = true;
        child.receiveShadow = true;
      }

      // Rest arms down to the sides (convert from T-pose to relaxed anatomical pose)
      if (child.name === 'mixamorig:LeftArm') {
        child.rotation.z = -1.25;
        child.rotation.x = 0.15;
      }
      if (child.name === 'mixamorig:RightArm') {
        child.rotation.z = 1.25;
        child.rotation.x = 0.15;
      }

      // Tilt head and neck back into CPR open airway / sniffing position
      if (child.name === 'mixamorig:Neck') {
        child.rotation.x = -0.3;
      }
      if (child.name === 'mixamorig:Head') {
        child.rotation.x = -0.35;
      }
    });

    return clone;
  }, [scene]);

  // Downward compression displacement
  const depression = isCPRActive ? Math.max(0, Math.sin(beatPhase * Math.PI) * 0.04) : 0;

  return (
    <group
      position={[0, -1.28 - depression * 0.5, 0]}
      rotation={[-0.15, 0, 0]}
      scale={[1.15, 1.15, 1.15]}
    >
      <primitive object={clonedScene} />
    </group>
  );
}

useGLTF.preload('/models/manikin.glb');
