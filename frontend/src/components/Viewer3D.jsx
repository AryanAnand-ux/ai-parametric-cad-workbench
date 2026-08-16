/**
 * Viewer3D.jsx — React Three Fiber 3D STL Viewer
 *
 * Features:
 *  - Loads STL files directly from backend static endpoint
 *  - Orbit controls (drag to rotate, scroll to zoom, right-drag to pan)
 *  - Auto-fit camera strictly to the STL mesh bounding sphere
 *  - Supports Solid / Wireframe render modes
 *  - Directional shadows, metallic material shader
 *  - Studio blueprint grid floor
 */

import { Suspense, useRef, useEffect, useState, useImperativeHandle, forwardRef } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, Grid, Center } from '@react-three/drei';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import * as THREE from 'three';

// ─────────────────────────────────────────────────────────────────────────────
// Inner mesh component — loads and renders one STL
// ─────────────────────────────────────────────────────────────────────────────

function STLMesh({ url, wireframe, onGeometryLoaded, onError }) {
  const [geometry, setGeometry] = useState(null);
  const geoRef = useRef(null);

  useEffect(() => {
    if (!url) return;

    const loader = new STLLoader();
    loader.load(
      url,
      (geo) => {
        geo.computeVertexNormals();
        geo.center();
        if (geoRef.current) geoRef.current.dispose();
        geoRef.current = geo;
        setGeometry(geo);
        if (onGeometryLoaded) onGeometryLoaded(geo);
      },
      undefined,
      (err) => {
        console.error('[STLMesh] Load error:', err);
        if (onError) onError(err);
      }
    );

    return () => {
      if (geoRef.current) {
        geoRef.current.dispose();
        geoRef.current = null;
      }
    };
  }, [url, onGeometryLoaded, onError]);

  if (!geometry) return null;

  return (
    <mesh geometry={geometry} castShadow receiveShadow>
      <meshStandardMaterial
        color="#3B82F6"
        roughness={0.25}
        metalness={0.4}
        wireframe={wireframe}
      />
    </mesh>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Camera auto-fit: computes exact distance from vertical FOV trigonometry
// Formula: distance = (sphere.radius / sin(vertical_FOV / 2)) * safety_margin
// ─────────────────────────────────────────────────────────────────────────────

const CameraController = forwardRef(function CameraController({ loadedGeometry }, ref) {
  const { camera, controls } = useThree();

  const resetCamera = () => {
    if (!loadedGeometry) return;
    loadedGeometry.computeBoundingSphere();
    const sphere = loadedGeometry.boundingSphere;
    if (!sphere || sphere.radius <= 0) return;

    // Exact trigonometric camera distance based on vertical Field of View
    const fovRad = (camera.fov * Math.PI) / 180;
    const trigDistance = (sphere.radius / Math.sin(fovRad / 2)) * 1.25; // 1.25 margin factor
    const dist = Math.max(trigDistance, 15);

    camera.position.set(dist, dist * 0.6, dist);
    camera.lookAt(sphere.center);
    if (controls) controls.target.copy(sphere.center);
    camera.near = Math.max(0.1, dist * 0.01);
    camera.far = dist * 100;
    camera.updateProjectionMatrix();
  };

  useImperativeHandle(ref, () => ({
    resetView: resetCamera
  }));

  useEffect(() => {
    resetCamera();
  }, [loadedGeometry]);

  return null;
});

// ─────────────────────────────────────────────────────────────────────────────
// Main Viewer Component
// ─────────────────────────────────────────────────────────────────────────────

const Viewer3D = forwardRef(function Viewer3D({ meshUrl, wireframe = false }, ref) {
  const [loadedGeometry, setLoadedGeometry] = useState(null);
  const cameraCtrlRef = useRef(null);

  useImperativeHandle(ref, () => ({
    resetView: () => {
      if (cameraCtrlRef.current) cameraCtrlRef.current.resetView();
    }
  }));

  const fullUrl = meshUrl
    ? (import.meta.env.VITE_API_URL
        ? `${import.meta.env.VITE_API_URL}${meshUrl}`
        : meshUrl)
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
      <ambientLight intensity={0.45} />
      <directionalLight
        position={[50, 80, 50]}
        intensity={1.6}
        castShadow
        shadow-mapSize={[2048, 2048]}
      />
      <directionalLight position={[-30, 40, -30]} intensity={0.5} color="#cbd5e1" />
      <pointLight position={[0, -40, 0]} intensity={0.3} color="#60a5fa" />

      {/* Studio Blueprint Grid floor */}
      <Grid
        position={[0, -0.01, 0]}
        args={[200, 200]}
        cellSize={5}
        cellThickness={1.2}
        cellColor="#c7c2b2"
        sectionSize={20}
        sectionThickness={2}
        sectionColor="#8c8573"
        fadeDistance={200}
        fadeStrength={1.5}
        infiniteGrid
      />

      {/* STL Model */}
      {fullUrl && (
        <Suspense fallback={null}>
          <Center>
            <STLMesh url={fullUrl} wireframe={wireframe} onGeometryLoaded={setLoadedGeometry} />
          </Center>
          <CameraController ref={cameraCtrlRef} loadedGeometry={loadedGeometry} />
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
});

export default Viewer3D;
