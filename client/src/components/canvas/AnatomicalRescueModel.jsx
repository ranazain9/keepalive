import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';

/**
 * AnatomicalRescueModel
 * Exact medical-grade resuscitation visualization matching Pinterest reference (https://pin.it/xAC3cOf1M).
 * - Real 3D photogrammetric human body in supine position (airway tilted, head left, chest up)
 * - Translucent holographic diagnostic shell showing facial profile (nose, lips, chin, neck, chest)
 * - Internal Brain with Cerebral Vascular Network (Circle of Willis) inside cranium
 * - Cervical & thoracic vertebral column (Spine)
 * - Common & Internal Carotid Arteries (Red) + Jugular Veins (Blue) connecting heart to brain
 * - Anatomical Heart & Ribcage inside thoracic cavity
 * - Dynamic Blood Perfusion Wave: on each compression beat, arterial pulse surges from heart to brain
 * - Rescuer Hands positioned vertically over lower sternum performing 2.2" compressions at 110 BPM
 */
export function AnatomicalRescueModel({ isCPRActive = false, beatPhase = 0 }) {
  // Load real 3D human body scan
  const { scene: humanScene } = useGLTF('/models/human_body.glb');

  const heartRef = useRef();
  const brainRef = useRef();
  const bloodPulsesRef = useRef([]);
  const handsRef = useRef();
  const sternumRef = useRef();

  // Compression displacement curve (0 to 1)
  const stroke = isCPRActive ? Math.max(0, Math.sin(beatPhase * Math.PI)) : 0;
  const compressionDepth = stroke * 0.038; // ~2.2 inches in model scale

  // Clone and configure human body shell with diagnostic X-ray translucent contour
  const bodyMesh = useMemo(() => {
    const clone = humanScene.clone(true);

    const xRaySkinMaterial = new THREE.MeshPhysicalMaterial({
      color: new THREE.Color('#162235'),
      emissive: new THREE.Color('#0A192F'),
      emissiveIntensity: 0.35,
      roughness: 0.18,
      metalness: 0.15,
      transmission: 0.86, // Highly translucent to reveal internal organs
      thickness: 0.45,
      opacity: 0.82,
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide,
    });

    clone.traverse((child) => {
      if (child.isMesh) {
        child.material = xRaySkinMaterial;
        child.castShadow = false;
        child.receiveShadow = false;
      }
    });

    return clone;
  }, [humanScene]);

  // Procedural Brain Geometry with left & right hemispheres and cerebellum
  const brainGeometry = useMemo(() => {
    const group = new THREE.Group();

    // Left hemisphere
    const leftHemiGeo = new THREE.SphereGeometry(0.042, 28, 24);
    leftHemiGeo.scale(1.18, 0.95, 0.82);

    // Right hemisphere
    const rightHemiGeo = new THREE.SphereGeometry(0.042, 28, 24);
    rightHemiGeo.scale(1.18, 0.95, 0.82);

    // Cerebellum
    const cerebellumGeo = new THREE.SphereGeometry(0.026, 20, 18);
    cerebellumGeo.scale(0.9, 0.75, 1.15);

    // Brainstem
    const stemGeo = new THREE.CylinderGeometry(0.012, 0.014, 0.035, 16);

    return { leftHemiGeo, rightHemiGeo, cerebellumGeo, stemGeo };
  }, []);

  // Procedural Carotid Artery & Jugular Vein paths (connecting aorta to skull base)
  const { carotidCurveL, carotidCurveR, jugularCurveL, jugularCurveR, spinePoints } = useMemo(() => {
    // Carotid Left: Aorta (-0.11, 0.015, 0.012) -> Neck (-0.24, 0.005, 0.015) -> Skull (-0.37, 0.01, 0.018) -> Brain
    const cL = new THREE.CatmullRomCurve3([
      new THREE.Vector3(-0.11, 0.012, 0.012),
      new THREE.Vector3(-0.16, 0.018, 0.014),
      new THREE.Vector3(-0.23, 0.008, 0.016),
      new THREE.Vector3(-0.30, 0.006, 0.018),
      new THREE.Vector3(-0.36, 0.012, 0.018),
      new THREE.Vector3(-0.41, 0.018, 0.014),
    ]);

    // Carotid Right (slightly deeper into Z)
    const cR = new THREE.CatmullRomCurve3([
      new THREE.Vector3(-0.11, 0.012, -0.012),
      new THREE.Vector3(-0.16, 0.018, -0.014),
      new THREE.Vector3(-0.23, 0.008, -0.016),
      new THREE.Vector3(-0.30, 0.006, -0.018),
      new THREE.Vector3(-0.36, 0.012, -0.018),
      new THREE.Vector3(-0.41, 0.018, -0.014),
    ]);

    // Jugular Veins (parallel, slightly lower/lateral)
    const jL = new THREE.CatmullRomCurve3([
      new THREE.Vector3(-0.10, -0.002, 0.022),
      new THREE.Vector3(-0.17, 0.005, 0.024),
      new THREE.Vector3(-0.24, -0.003, 0.025),
      new THREE.Vector3(-0.31, -0.002, 0.026),
      new THREE.Vector3(-0.37, 0.005, 0.024),
    ]);

    const jR = new THREE.CatmullRomCurve3([
      new THREE.Vector3(-0.10, -0.002, -0.022),
      new THREE.Vector3(-0.17, 0.005, -0.024),
      new THREE.Vector3(-0.24, -0.003, -0.025),
      new THREE.Vector3(-0.31, -0.002, -0.026),
      new THREE.Vector3(-0.37, 0.005, -0.024),
    ]);

    // Cervical & Thoracic Vertebrae positions (C1-C7 + T1-T4)
    const sPts = [];
    for (let i = 0; i < 11; i++) {
      const t = i / 10;
      // Follow posterior contour of neck and upper back
      const x = -0.37 + t * 0.32;
      const y = -0.028 + Math.sin(t * Math.PI * 0.8) * 0.008 - (t > 0.6 ? 0.012 : 0);
      sPts.push(new THREE.Vector3(x, y, 0));
    }

    return {
      carotidCurveL: cL,
      carotidCurveR: cR,
      jugularCurveL: jL,
      jugularCurveR: jR,
      spinePoints: sPts,
    };
  }, []);

  // Procedural Rib Cage arches
  const ribsData = useMemo(() => {
    const ribs = [];
    // 6 pairs of prominent ribs
    for (let r = 0; r < 6; r++) {
      const xBase = -0.18 + r * 0.028;
      const ribCurveL = new THREE.CatmullRomCurve3([
        new THREE.Vector3(xBase, -0.032, 0.008),
        new THREE.Vector3(xBase - 0.006, -0.005, 0.052),
        new THREE.Vector3(xBase + 0.015, 0.038, 0.048),
        new THREE.Vector3(xBase + 0.025, 0.052, 0.012),
      ]);
      const ribCurveR = new THREE.CatmullRomCurve3([
        new THREE.Vector3(xBase, -0.032, -0.008),
        new THREE.Vector3(xBase - 0.006, -0.005, -0.052),
        new THREE.Vector3(xBase + 0.015, 0.038, -0.048),
        new THREE.Vector3(xBase + 0.025, 0.052, -0.012),
      ]);
      ribs.push({ ribCurveL, ribCurveR, id: r });
    }
    return ribs;
  }, []);

  // Cerebral Cortical Arteries (radiating branches over cerebral cortex)
  const brainBranches = useMemo(() => {
    const branches = [];
    for (let i = 0; i < 8; i++) {
      const angle = (i / 8) * Math.PI * 2;
      const r = 0.036;
      const xTarget = -0.41 + Math.cos(angle) * 0.032;
      const yTarget = 0.022 + Math.sin(angle) * 0.028;
      const zTarget = 0.025 * (i % 2 === 0 ? 1 : -1);

      const curve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(-0.39, 0.012, zTarget * 0.4),
        new THREE.Vector3(-0.40, 0.018, zTarget * 0.8),
        new THREE.Vector3(xTarget, yTarget, zTarget),
      ]);
      branches.push(curve);
    }
    return branches;
  }, []);

  // Blood pulse packets along carotid arteries
  const pulsePositions = [0.15, 0.4, 0.65, 0.9];

  // Dynamic animation updates per frame
  useFrame(({ clock }) => {
    const time = clock.getElapsedTime();

    // Heart compression and rhythm
    if (heartRef.current) {
      if (isCPRActive) {
        // Compress down in Y and flatten slightly during chest compression stroke
        heartRef.current.scale.y = 1.0 - stroke * 0.32;
        heartRef.current.scale.x = 1.0 + stroke * 0.15;
        heartRef.current.position.y = 0.008 - compressionDepth * 0.7;
      } else {
        // Subtle resting baseline pulse
        const restBeat = Math.sin(time * 3.5) * 0.04;
        heartRef.current.scale.set(1 + restBeat, 1 + restBeat, 1 + restBeat);
        heartRef.current.position.y = 0.008;
      }
    }

    // Brain cerebral perfusion glow
    if (brainRef.current) {
      const brainMatL = brainRef.current.children[0]?.material;
      const brainMatR = brainRef.current.children[1]?.material;
      if (brainMatL && brainMatR) {
        if (isCPRActive) {
          // Oxygenated pulse wave lights up the brain on each systolic stroke
          const perfusionPulse = Math.pow(stroke, 1.6);
          const intensity = 0.4 + perfusionPulse * 1.8;
          brainMatL.emissiveIntensity = intensity;
          brainMatR.emissiveIntensity = intensity;
          brainMatL.emissive.setRGB(0.95 * perfusionPulse, 0.2 * perfusionPulse, 0.25 * perfusionPulse);
          brainMatR.emissive.setRGB(0.95 * perfusionPulse, 0.2 * perfusionPulse, 0.25 * perfusionPulse);
        } else {
          brainMatL.emissiveIntensity = 0.2;
          brainMatR.emissiveIntensity = 0.2;
          brainMatL.emissive.set('#4B1E28');
          brainMatR.emissive.set('#4B1E28');
        }
      }
    }

    // Dynamic blood pulse positions along the carotid curve
    bloodPulsesRef.current.forEach((mesh, idx) => {
      if (!mesh) return;
      if (isCPRActive) {
        mesh.visible = true;
        // Travel from chest (t=0) to brain (t=1) synced to beatPhase
        const t = (beatPhase + idx * 0.25) % 1.0;
        const pt = carotidCurveL.getPointAt(t);
        mesh.position.copy(pt);
        mesh.scale.setScalar(0.7 + Math.sin(t * Math.PI) * 0.6);
      } else {
        mesh.visible = false;
      }
    });

    // Sternum depression under hands
    if (sternumRef.current) {
      sternumRef.current.position.y = 0.06 - compressionDepth;
    }

    // Hands displacement: pressing down onto sternum
    if (handsRef.current) {
      handsRef.current.position.y = 0.075 - compressionDepth;
    }
  });

  return (
    <group
      position={[0.12, -0.02, 0]}
      scale={[2.3, 2.3, 2.3]}
    >
      {/* ====================================================================
          1. REAL 3D HUMAN BODY MESH (Oriented Supine: Head Left, Chest Up)
          ==================================================================== */}
      <group
        rotation={[0, 0, Math.PI / 2]} // Lay supine horizontally
        position={[0, 0, 0]}
      >
        <primitive object={bodyMesh} />
      </group>

      {/* ====================================================================
          2. INTERNAL CRANIUM & BRAIN WITH CEREBRAL VASCULATURE
          ==================================================================== */}
      <group ref={brainRef} position={[-0.41, 0.022, 0]}>
        {/* Left Cerebral Hemisphere */}
        <mesh position={[0, 0, 0.02]}>
          <primitive object={brainGeometry.leftHemiGeo} attach="geometry" />
          <meshStandardMaterial
            color="#D67D89"
            roughness={0.4}
            metalness={0.08}
            emissive="#7A2234"
            emissiveIntensity={0.3}
          />
        </mesh>

        {/* Right Cerebral Hemisphere */}
        <mesh position={[0, 0, -0.02]}>
          <primitive object={brainGeometry.rightHemiGeo} attach="geometry" />
          <meshStandardMaterial
            color="#D67D89"
            roughness={0.4}
            metalness={0.08}
            emissive="#7A2234"
            emissiveIntensity={0.3}
          />
        </mesh>

        {/* Cerebellum (Posterior/Inferior) */}
        <mesh position={[0.038, -0.022, 0]}>
          <primitive object={brainGeometry.cerebellumGeo} attach="geometry" />
          <meshStandardMaterial color="#B86572" roughness={0.45} />
        </mesh>

        {/* Brainstem into Spinal Cord */}
        <mesh position={[0.038, -0.042, 0]} rotation={[0, 0, 0.2]}>
          <primitive object={brainGeometry.stemGeo} attach="geometry" />
          <meshStandardMaterial color="#E2B4B9" roughness={0.35} />
        </mesh>

        {/* Cortical Blood Vessels radiating over brain lobes */}
        {brainBranches.map((curve, idx) => (
          <mesh key={`brain-vessel-${idx}`}>
            <tubeGeometry args={[curve, 16, 0.0018, 8, false]} />
            <meshStandardMaterial
              color={idx % 2 === 0 ? '#EF4444' : '#0284C7'}
              emissive={idx % 2 === 0 ? '#EF4444' : '#0284C7'}
              emissiveIntensity={isCPRActive ? 1.5 : 0.6}
              roughness={0.2}
            />
          </mesh>
        ))}
      </group>

      {/* ====================================================================
          3. CERVICAL & UPPER THORACIC SPINE (Vertebrae Column)
          ==================================================================== */}
      <group>
        {spinePoints.map((pt, idx) => (
          <group key={`vertebra-${idx}`} position={pt}>
            {/* Vertebral body */}
            <mesh scale={[1.1, 0.7, 1.0]}>
              <cylinderGeometry args={[0.012, 0.013, 0.018, 14]} />
              <meshStandardMaterial color="#E2E8F0" roughness={0.5} metalness={0.1} />
            </mesh>
            {/* Spinous process pointing downward */}
            <mesh position={[0, -0.012, 0]} rotation={[0, 0, -0.3]}>
              <coneGeometry args={[0.007, 0.016, 8]} />
              <meshStandardMaterial color="#CBD5E1" roughness={0.5} />
            </mesh>
            {/* Intervertebral disc */}
            <mesh position={[0.014, 0, 0]}>
              <cylinderGeometry args={[0.011, 0.011, 0.004, 12]} />
              <meshStandardMaterial color="#94A3B8" roughness={0.6} />
            </mesh>
          </group>
        ))}
      </group>

      {/* ====================================================================
          4. CAROTID ARTERIES (RED) & JUGULAR VEINS (BLUE)
          ==================================================================== */}
      {/* Left Common & Internal Carotid Artery (Oxygenated blood to brain) */}
      <mesh>
        <tubeGeometry args={[carotidCurveL, 36, 0.0045, 12, false]} />
        <meshStandardMaterial
          color="#EF4444"
          emissive="#DC2626"
          emissiveIntensity={isCPRActive ? 1.6 : 0.8}
          roughness={0.25}
          metalness={0.1}
        />
      </mesh>

      {/* Right Carotid Artery */}
      <mesh>
        <tubeGeometry args={[carotidCurveR, 36, 0.0045, 12, false]} />
        <meshStandardMaterial
          color="#EF4444"
          emissive="#DC2626"
          emissiveIntensity={isCPRActive ? 1.6 : 0.8}
          roughness={0.25}
          metalness={0.1}
        />
      </mesh>

      {/* Left Internal Jugular Vein (Deoxygenated return blood) */}
      <mesh>
        <tubeGeometry args={[jugularCurveL, 32, 0.005, 12, false]} />
        <meshStandardMaterial
          color="#0284C7"
          emissive="#0369A1"
          emissiveIntensity={0.6}
          roughness={0.3}
          metalness={0.1}
        />
      </mesh>

      {/* Right Jugular Vein */}
      <mesh>
        <tubeGeometry args={[jugularCurveR, 32, 0.005, 12, false]} />
        <meshStandardMaterial
          color="#0284C7"
          emissive="#0369A1"
          emissiveIntensity={0.6}
          roughness={0.3}
          metalness={0.1}
        />
      </mesh>

      {/* Dynamic arterial blood pulse packets surging from heart to brain */}
      {pulsePositions.map((_, idx) => (
        <mesh
          key={`blood-pulse-${idx}`}
          ref={(el) => (bloodPulsesRef.current[idx] = el)}
        >
          <sphereGeometry args={[0.006, 12, 12]} />
          <meshBasicMaterial color="#FF4D4D" />
        </mesh>
      ))}

      {/* ====================================================================
          5. THORACIC CAVITY: HEART & RIBS
          ==================================================================== */}
      {/* Anatomical Heart beneath sternum */}
      <group ref={heartRef} position={[-0.09, 0.015, 0.008]}>
        {/* Left & Right Ventricles (cardiac apex) */}
        <mesh position={[0, -0.008, 0]} rotation={[0, 0, 0.4]} scale={[1.1, 1.3, 0.9]}>
          <coneGeometry args={[0.026, 0.052, 18]} />
          <meshStandardMaterial
            color="#B91C1C"
            roughness={0.35}
            emissive={isCPRActive ? '#DC2626' : '#991B1B'}
            emissiveIntensity={isCPRActive ? 0.9 : 0.3}
          />
        </mesh>

        {/* Atria base */}
        <mesh position={[-0.012, 0.018, 0]} scale={[1.1, 0.8, 1.0]}>
          <sphereGeometry args={[0.025, 18, 16]} />
          <meshStandardMaterial color="#991B1B" roughness={0.38} />
        </mesh>

        {/* Aortic Arch emerging from heart */}
        <mesh position={[-0.018, 0.026, 0]} rotation={[0, 0, -0.6]}>
          <torusGeometry args={[0.016, 0.0065, 12, 20, Math.PI * 0.9]} />
          <meshStandardMaterial
            color="#EF4444"
            emissive="#EF4444"
            emissiveIntensity={1.2}
            roughness={0.25}
          />
        </mesh>

        {/* Pulmonary Trunk */}
        <mesh position={[0.008, 0.022, 0.014]} rotation={[0.4, 0.3, 0.5]}>
          <cylinderGeometry args={[0.0055, 0.006, 0.028, 12]} />
          <meshStandardMaterial color="#0284C7" roughness={0.3} />
        </mesh>
      </group>

      {/* Anatomical Rib Cage */}
      <group>
        {ribsData.map((r) => (
          <group key={`rib-pair-${r.id}`}>
            <mesh>
              <tubeGeometry args={[r.ribCurveL, 20, 0.0035, 8, false]} />
              <meshStandardMaterial
                color="#E2E8F0"
                roughness={0.4}
                opacity={0.88}
                transparent={true}
              />
            </mesh>
            <mesh>
              <tubeGeometry args={[r.ribCurveR, 20, 0.0035, 8, false]} />
              <meshStandardMaterial
                color="#E2E8F0"
                roughness={0.4}
                opacity={0.88}
                transparent={true}
              />
            </mesh>
          </group>
        ))}
      </group>

      {/* Sternum (Chest Bone Plate) */}
      <mesh ref={sternumRef} position={[-0.10, 0.06, 0]} rotation={[0, 0, 0]}>
        <boxGeometry args={[0.13, 0.008, 0.028]} />
        <meshStandardMaterial color="#F1F5F9" roughness={0.35} />
      </mesh>

      {/* ====================================================================
          6. RESCUER'S COMPRESSING HANDS (Over Sternum, Compressing at 110 BPM)
          ==================================================================== */}
      <group ref={handsRef} position={[-0.10, 0.08, 0]}>
        {/* Heel of Palm on Sternum */}
        <mesh position={[0, 0.008, 0]} scale={[1.2, 0.45, 1.1]}>
          <sphereGeometry args={[0.028, 18, 16]} />
          <meshStandardMaterial color="#DDB29E" roughness={0.48} />
        </mesh>

        {/* Lower Fingers fanning over patient's chest */}
        {[-0.016, -0.005, 0.006, 0.017].map((zOff, i) => (
          <mesh
            key={`lower-finger-${i}`}
            position={[0.026, 0.006, zOff]}
            rotation={[0, 0, -0.3]}
          >
            <cylinderGeometry args={[0.004, 0.0045, 0.038, 10]} />
            <meshStandardMaterial color="#DDB29E" roughness={0.48} />
          </mesh>
        ))}

        {/* Interlaced Top Hand */}
        <mesh position={[0.006, 0.022, 0.004]} scale={[1.15, 0.5, 1.1]}>
          <sphereGeometry args={[0.029, 18, 16]} />
          <meshStandardMaterial color="#E2B7A3" roughness={0.48} />
        </mesh>

        {/* Top Hand Interlacing Fingers */}
        {[-0.014, -0.003, 0.008, 0.019].map((zOff, i) => (
          <mesh
            key={`upper-finger-${i}`}
            position={[0.018, 0.024, zOff]}
            rotation={[0.1, 0, -0.2]}
          >
            <cylinderGeometry args={[0.0042, 0.0046, 0.036, 10]} />
            <meshStandardMaterial color="#E2B7A3" roughness={0.48} />
          </mesh>
        ))}

        {/* Rescuer Vertical Forearms (90° Locked Elbows) */}
        <mesh position={[0.004, 0.12, 0.01]} rotation={[0, 0, -0.05]}>
          <cylinderGeometry args={[0.018, 0.015, 0.18, 16]} />
          <meshStandardMaterial color="#DDB29E" roughness={0.5} />
        </mesh>
        <mesh position={[-0.008, 0.12, -0.01]} rotation={[0, 0, 0.05]}>
          <cylinderGeometry args={[0.017, 0.014, 0.18, 16]} />
          <meshStandardMaterial color="#E2B7A3" roughness={0.5} />
        </mesh>
      </group>
    </group>
  );
}

useGLTF.preload('/models/human_body.glb');
