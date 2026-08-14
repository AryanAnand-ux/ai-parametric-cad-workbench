/**
 * Viewer3D.jsx — React Three Fiber 3D STL Viewer
 *
 * Features:
 *  - Loads STL files directly from the backend static endpoint
 *  - Orbit controls (drag to rotate, scroll to zoom, right-drag to pan)
 *  - Auto-fit camera to model bounding sphere on load
 *  - Directional shadows, metallic material shader
 *  - Infinite grid floor
 */

import { Suspense, useRef, useEffect, useState } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, Grid, Center } from '@react-three/drei';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import * as THREE from 'three';

// ─────────────────────────────────────────────────────────────────────────────
// Inner mesh component — loads and renders one STL
// Geometry stored in a ref to avoid stale-closure on cleanup
// ─────────────────────────────────────────────────────────────────────────────

function STLMesh({ url }) {
  const [geometry, setGeometry] = useState(null);
  const geoRef = useRef(null);    // ref so cleanup always sees latest geo

  useEffect(() => {
    if (!url) return;

    const loader = new STLLoader();
    loader.load(
      url,
      (geo) => {
        geo.computeVertexNormals();
        geo.center();
        // Dispose old geometry before replacing
        if (geoRef.current) geoRef.current.dispose();
        geoRef.current = geo;
        setGeometry(geo);
      },
      undefined,
      (err) => console.error('[STLMesh] Load error:', err)
    );

    return () => {
      if (geoRef.current) {
        geoRef.current.dispose();
        geoRef.current = null;
      }
    };
  }, [url]);

  if (!geometry) return null;

  return (
    <mesh geometry={geometry} castShadow receiveShadow>
      <meshStandardMaterial
        color="#4f8ef7"
        roughness={0.35}
        metalness={0.65}
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

    const timeout = setTimeout(() => {
      const box = new THREE.Box3().setFromObject(scene);
      if (box.isEmpty()) return;
      const sphere = box.getBoundingSphere(new THREE.Sphere());
      const dist = Math.max(sphere.radius * 2.8, 10);
      camera.position.set(dist, dist * 0.6, dist);
      camera.lookAt(sphere.center);
      camera.near = dist * 0.01;
      camera.far = dist * 100;
      camera.updateProjectionMatrix();
    }, 150);

    return () => clearTimeout(timeout);
  }, [url, camera, scene]);

  return null;
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Viewer Component
// ─────────────────────────────────────────────────────────────────────────────

export default function Viewer3D({ meshUrl }) {
  // When using the Vite dev proxy, /static/* is forwarded to backend.
  // In production, set VITE_API_URL so STL_URL builds a full URL.
  const fullUrl = meshUrl
    ? (import.meta.env.VITE_API_URL
        ? `${import.meta.env.VITE_API_URL}${meshUrl}`
        : meshUrl)          // relative path works via Vite proxy in dev
    : null;

  return (
    <Canvas
      className="viewer-canvas"
      shadows
      camera={{ position: [80, 60, 80], fov: 45 }}
      gl={{ antialias: true, alpha: false }}
      style={{ background: 'transparent' }}
    >
      {/* Lighting */}
      <ambientLight intensity={0.35} />
      <directionalLight
        position={[50, 80, 50]}
        intensity={1.5}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
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
        minDistance={1}
        maxDistance={5000}
        makeDefault
      />
    </Canvas>
  );
}
