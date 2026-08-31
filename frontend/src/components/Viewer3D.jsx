/**
 * Viewer3D.jsx — React Three Fiber 3D STL CAD Viewer
 *
 * Features:
 *  - Loads binary/ASCII STL files directly from backend static endpoint
 *  - Orbit controls (drag to rotate, scroll to zoom, right-drag to pan)
 *  - Camera view presets: Top, Front, Side, Isometric, and Auto-Fit
 *  - PBR Material presets: Machined Aluminum, Blueprint Blue, Tooling Orange, Carbon Slate
 *  - Supports Solid / Wireframe render modes + Coordinate Axes Helper
 *  - Studio blueprint millimeter grid floor + Directional PCF soft shadows
 */

import { Suspense, useRef, useEffect, useState, useImperativeHandle, forwardRef } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, Grid, Center, Html } from '@react-three/drei';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import * as THREE from 'three';

// ─────────────────────────────────────────────────────────────────────────────
// Material Presets
// ─────────────────────────────────────────────────────────────────────────────
export const MATERIAL_PRESETS = {
  blue: {
    name: 'CAD Blue',
    color: '#2563EB',
    roughness: 0.3,
    metalness: 0.25,
    icon: '🟦'
  },
  aluminum: {
    name: 'Machined Aluminum',
    color: '#CBD5E1',
    roughness: 0.2,
    metalness: 0.85,
    icon: '⚙️'
  },
  yellow: {
    name: 'Tooling Yellow',
    color: '#EAB308',
    roughness: 0.35,
    metalness: 0.1,
    icon: '🟨'
  },
  dark: {
    name: 'Carbon Slate',
    color: '#334155',
    roughness: 0.5,
    metalness: 0.3,
    icon: '⬛'
  }
};

// ─────────────────────────────────────────────────────────────────────────────
// 3D Bounding Box Dimension Annotations (Phase 4 Deliverable)
// ─────────────────────────────────────────────────────────────────────────────
function DimensionBoundingBox({ geometry, visible = true }) {
  if (!geometry || !visible) return null;

  geometry.computeBoundingBox();
  const box = geometry.boundingBox;
  if (!box) return null;

  const size = new THREE.Vector3();
  box.getSize(size);
  if (size.x <= 0 && size.y <= 0 && size.z <= 0) return null;

  const dimX = size.x.toFixed(1);
  const dimY = size.y.toFixed(1);
  const dimZ = size.z.toFixed(1);

  return (
    <group>
      {/* 3D Wireframe Bounding Box */}
      <lineSegments>
        <edgesGeometry args={[new THREE.BoxGeometry(size.x, size.y, size.z)]} />
        <lineBasicMaterial color="#3B82F6" transparent opacity={0.35} />
      </lineSegments>

      {/* X dimension badge (Length) */}
      <Html position={[0, -size.y / 2 - 3, size.z / 2 + 2]} center distanceFactor={140}>
        <div className="dimension-badge x-badge">
          <span className="dim-axis">L:</span> {dimX}mm
        </div>
      </Html>

      {/* Y dimension badge (Height) */}
      <Html position={[-size.x / 2 - 3, 0, size.z / 2 + 2]} center distanceFactor={140}>
        <div className="dimension-badge y-badge">
          <span className="dim-axis">H:</span> {dimY}mm
        </div>
      </Html>

      {/* Z dimension badge (Depth / Width) */}
      <Html position={[size.x / 2 + 3, -size.y / 2 - 3, 0]} center distanceFactor={140}>
        <div className="dimension-badge z-badge">
          <span className="dim-axis">W:</span> {dimZ}mm
        </div>
      </Html>
    </group>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Inner Mesh Component
// ─────────────────────────────────────────────────────────────────────────────
function STLMesh({ url, wireframe, materialType = 'blue', onGeometryLoaded, onError }) {
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

  const mat = MATERIAL_PRESETS[materialType] || MATERIAL_PRESETS.blue;

  return (
    <mesh geometry={geometry} castShadow receiveShadow>
      <meshStandardMaterial
        color={mat.color}
        roughness={mat.roughness}
        metalness={mat.metalness}
        wireframe={wireframe}
      />
    </mesh>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Camera Controller with View Presets
// ─────────────────────────────────────────────────────────────────────────────
const CameraController = forwardRef(function CameraController({ loadedGeometry }, ref) {
  const { camera, controls } = useThree();

  const getFitDistance = () => {
    if (!loadedGeometry) return 80;
    loadedGeometry.computeBoundingSphere();
    const sphere = loadedGeometry.boundingSphere;
    if (!sphere || sphere.radius <= 0) return 80;

    const fovRad = (camera.fov * Math.PI) / 180;
    const trigDistance = (sphere.radius / Math.sin(fovRad / 2)) * 1.35;
    return Math.max(trigDistance, 20);
  };

  const setView = (viewType) => {
    const dist = getFitDistance();
    const target = new THREE.Vector3(0, 0, 0);

    if (viewType === 'top') {
      camera.position.set(0, dist * 1.4, 0.001);
    } else if (viewType === 'front') {
      camera.position.set(0, 0, dist * 1.4);
    } else if (viewType === 'side') {
      camera.position.set(dist * 1.4, 0, 0);
    } else {
      // Isometric default
      camera.position.set(dist * 0.8, dist * 0.7, dist * 0.8);
    }

    camera.lookAt(target);
    if (controls) {
      controls.target.copy(target);
      controls.update();
    }
    camera.near = Math.max(0.1, dist * 0.01);
    camera.far = dist * 100;
    camera.updateProjectionMatrix();
  };

  useImperativeHandle(ref, () => ({
    resetView: () => setView('iso'),
    setCameraView: (type) => setView(type)
  }));

  useEffect(() => {
    if (loadedGeometry) {
      setView('iso');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadedGeometry]);

  return null;
});

// ─────────────────────────────────────────────────────────────────────────────
// Main Viewer Component
// ─────────────────────────────────────────────────────────────────────────────
const Viewer3D = forwardRef(function Viewer3D(
  {
    meshUrl,
    wireframe = false,
    materialType = 'blue',
    showAxes = true,
    showDimensions = true
  },
  ref
) {
  const [loadedGeometry, setLoadedGeometry] = useState(null);
  const cameraCtrlRef = useRef(null);

  useImperativeHandle(ref, () => ({
    resetView: () => cameraCtrlRef.current?.resetView(),
    setCameraView: (type) => cameraCtrlRef.current?.setCameraView(type)
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
      gl={{ antialias: true, alpha: false, preserveDrawingBuffer: true }}
      style={{ background: 'transparent' }}
    >
      {/* Studio Lighting */}
      <ambientLight intensity={0.55} />
      <directionalLight
        position={[60, 90, 60]}
        intensity={1.8}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-bias={-0.0001}
      />
      <directionalLight position={[-40, 50, -40]} intensity={0.7} color="#cbd5e1" />
      <directionalLight position={[0, -50, 0]} intensity={0.25} color="#94a3b8" />

      {/* Studio Blueprint Grid floor */}
      <Grid
        position={[0, -0.01, 0]}
        args={[250, 250]}
        cellSize={5}
        cellThickness={1.2}
        cellColor="#CBD5E1"
        sectionSize={25}
        sectionThickness={2.2}
        sectionColor="#94A3B8"
        fadeDistance={250}
        fadeStrength={1.2}
        infiniteGrid
      />

      {/* Coordinate Axes Helper */}
      {showAxes && <axesHelper args={[40]} />}

      {/* STL Solid Model + Dimension Annotations */}
      {fullUrl && (
        <Suspense fallback={null}>
          <Center>
            <STLMesh
              url={fullUrl}
              wireframe={wireframe}
              materialType={materialType}
              onGeometryLoaded={setLoadedGeometry}
            />
            <DimensionBoundingBox geometry={loadedGeometry} visible={showDimensions} />
          </Center>
          <CameraController ref={cameraCtrlRef} loadedGeometry={loadedGeometry} />
        </Suspense>
      )}

      {/* Orbit Controls */}
      <OrbitControls
        enableDamping
        dampingFactor={0.08}
        screenSpacePanning={false}
        minDistance={2}
        maxDistance={5000}
        makeDefault
      />
    </Canvas>
  );
});

export default Viewer3D;

