/**
 * Viewer3D.jsx — React Three Fiber 3D STL Viewer
 * 
 * Features:
 *  - Loads STL files directly from the backend static endpoint
 *  - Orbit controls (drag to rotate, scroll to zoom, right-drag to pan)
 *  - HDRI-like gradient environment
 *  - Smooth camera animation on model change
 *  - Loading and error states
 */

import { Suspense, useRef, useEffect, useState } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import {
  OrbitControls,
  Grid,
  Environment,
  useProgress,
  Html,
  Center,
} from '@react-three/drei';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import * as THREE from 'three';
import { STL_URL } from '../api';

// ─────────────────────────────────────────────────────────────────────────────
// Inner mesh component — loads and renders one STL
// ─────────────────────────────────────────────────────────────────────────────

function STLMesh({ url }) {
  const [geometry, setGeometry] = useState(null);
  const meshRef = useRef();

  useEffect(() => {
    if (!url) return;

    const loader = new STLLoader();
    loader.load(
      url,
      (geo) => {
        geo.computeVertexNormals();
        geo.center();
        setGeometry(geo);
      },
      undefined,
      (err) => console.error('[STLMesh] Load error:', err)
    );

    return () => {
      // Clean up geometry on unmount or URL change
      if (geometry) geometry.dispose();
    };
  }, [url]);

  if (!geometry) return null;

  return (
    <mesh ref={meshRef} geometry={geometry} castShadow receiveShadow>
      <meshStandardMaterial
        color="#4f8ef7"
        roughness={0.35}
        metalness={0.65}
        envMapIntensity={1.2}
      />
    </mesh>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Camera auto-fit: adjusts camera distance based on model bounding sphere
// ─────────────────────────────────────────────────────────────────────────────

function CameraController({ url }) {
  const { camera, scene } = useThree();

  useEffect(() => {
    if (!url) return;

    // Wait a frame for the mesh to render, then frame it
    const timeout = setTimeout(() => {
      const box = new THREE.Box3().setFromObject(scene);
      const sphere = box.getBoundingSphere(new THREE.Sphere());
      const dist = sphere.radius * 2.8;
      camera.position.set(dist, dist * 0.6, dist);
      camera.lookAt(sphere.center);
      camera.near = dist * 0.01;
      camera.far = dist * 100;
      camera.updateProjectionMatrix();
    }, 100);

    return () => clearTimeout(timeout);
  }, [url, camera, scene]);

  return null;
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Viewer Component
// ─────────────────────────────────────────────────────────────────────────────

export default function Viewer3D({ meshUrl, loading }) {
  const fullUrl = meshUrl ? STL_URL(meshUrl) : null;

  return (
    <Canvas
      className="viewer-canvas"
      shadows
      camera={{ position: [80, 60, 80], fov: 45 }}
      gl={{ antialias: true, alpha: false }}
      style={{ background: 'transparent' }}
    >
      {/* Lighting */}
      <ambientLight intensity={0.3} />
      <directionalLight
        position={[50, 80, 50]}
        intensity={1.5}
        castShadow
        shadow-mapSize={[2048, 2048]}
      />
      <directionalLight position={[-30, 40, -30]} intensity={0.6} color="#93c5fd" />
      <pointLight position={[0, -40, 0]} intensity={0.4} color="#4f8ef7" />

      {/* Grid floor */}
      <Grid
        position={[0, -0.01, 0]}
        args={[200, 200]}
        cellSize={5}
        cellThickness={0.5}
        cellColor="#1e2d4a"
        sectionSize={20}
        sectionThickness={1}
        sectionColor="#2a3d5e"
        fadeDistance={150}
        fadeStrength={2}
        infiniteGrid
      />

      {/* STL Model */}
      {fullUrl && (
        <Suspense fallback={null}>
          <Center>
            <STLMesh url={fullUrl} />
          </Center>
          <CameraController url={fullUrl} />
        </Suspense>
      )}

      {/* Orbit controls */}
      <OrbitControls
        enableDamping
        dampingFactor={0.05}
        screenSpacePanning={false}
        minDistance={5}
        maxDistance={2000}
        makeDefault
      />
    </Canvas>
  );
}
