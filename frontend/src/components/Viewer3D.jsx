/**
 * Viewer3D.jsx — AutoCAD-Engineered React Three Fiber 3D CAD Viewer
 *
 * Professional CAD Features:
 *  - "Shaded with Visible Edges" rendering using crisp THREE.EdgesGeometry (24° threshold)
 *  - Interactive 3D AutoCAD ViewCube (top-right) with click-to-orient camera views
 *  - AutoCAD WCS/UCS 3D coordinate tripod (bottom-left) with labeled RGB axes
 *  - Authentic AutoCAD 3D model space dark slate gradient background & millimeter snap grid
 *  - Red/Green origin crosshair axes passing through (0, 0, 0)
 *  - Multiple AutoCAD visual styles: Shaded with Edges, Realistic, Conceptual, X-Ray, Wireframe
 *  - Real-time CAD coordinate tracking and bounding box dimension badges
 */

import { Suspense, useRef, useEffect, useState, useMemo, useCallback, useImperativeHandle, forwardRef } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import {
  OrbitControls,
  Grid,
  Center,
  Html,
  GizmoHelper,
  GizmoViewcube,
  GizmoViewport,
} from '@react-three/drei';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import * as THREE from 'three';

import { MATERIAL_PRESETS } from '../constants/materials';
import { VISUAL_STYLES, VIEWPORT_BACKGROUNDS } from '../constants/visualStyles';
import { resolveAssetUrl } from '../api';

export { MATERIAL_PRESETS };

// ─────────────────────────────────────────────────────────────────────────────
// AutoCAD Origin Crosshair Lines (X: Red, Y/Z: Green)
// ─────────────────────────────────────────────────────────────────────────────
function AutoCADOriginAxes({ length = 150, visible = true }) {
  if (!visible) return null;

  return (
    <group position={[0, 0.002, 0]}>
      {/* X Axis (Red) */}
      <lineSegments>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={2}
            array={new Float32Array([-length, 0, 0, length, 0, 0])}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial color="#EF4444" linewidth={2} transparent opacity={0.65} />
      </lineSegments>

      {/* Y/Z Axis (Green) */}
      <lineSegments>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={2}
            array={new Float32Array([0, 0, -length, 0, 0, length])}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial color="#22C55E" linewidth={2} transparent opacity={0.65} />
      </lineSegments>
    </group>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 3D Bounding Box Dimension Annotations
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
        <lineBasicMaterial color="#38BDF8" transparent opacity={0.4} />
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
// Inner Mesh Component with AutoCAD "Shaded with Visible Edges" Engine
// ─────────────────────────────────────────────────────────────────────────────
function STLMesh({
  url,
  visualStyle = 'shaded_edges',
  materialType = 'cad_gray',
  onGeometryLoaded,
  onError,
}) {
  const [geometry, setGeometry] = useState(null);
  const geoRef = useRef(null);

  useEffect(() => {
    if (!url) return;

    let disposed = false;
    setGeometry(null);
    const loader = new STLLoader();
    loader.load(
      url,
      (geo) => {
        if (disposed) {
          geo.dispose();
          return;
        }
        geo.computeVertexNormals();
        geo.center();
        if (geoRef.current) geoRef.current.dispose();
        geoRef.current = geo;
        setGeometry(geo);
        if (onGeometryLoaded) onGeometryLoaded(geo);
      },
      undefined,
      (err) => {
        if (disposed) return;
        console.error('[STLMesh] Load error:', err);
        if (onError) onError(err);
      }
    );

    return () => {
      disposed = true;
      if (geoRef.current) {
        geoRef.current.dispose();
        geoRef.current = null;
      }
    };
  }, [url, onGeometryLoaded, onError]);

  // Extract sharp mechanical feature edges (>24 deg) without triangulating curved faces
  const edgesGeo = useMemo(() => {
    if (!geometry) return null;
    return new THREE.EdgesGeometry(geometry, 24);
  }, [geometry]);

  if (!geometry) return null;

  const matConfig = MATERIAL_PRESETS[materialType] || MATERIAL_PRESETS.cad_gray;
  const styleConfig = VISUAL_STYLES[visualStyle] || VISUAL_STYLES.shaded_edges;

  const isWireframe = styleConfig.wireframe;
  const showEdges = styleConfig.showEdges && !isWireframe;
  const isXRay = visualStyle === 'xray';
  const isConceptual = visualStyle === 'conceptual';

  const solidColor = isConceptual ? '#9CA3AF' : matConfig.color;
  const solidRoughness = isConceptual ? 0.6 : matConfig.roughness;
  const solidMetalness = isConceptual ? 0.15 : matConfig.metalness;

  const edgeColor = isXRay ? '#60A5FA' : (isConceptual ? '#1E293B' : '#0B0F19');

  return (
    <group>
      {/* Solid Shaded Geometry */}
      <mesh geometry={geometry} castShadow receiveShadow>
        <meshStandardMaterial
          color={solidColor}
          roughness={solidRoughness}
          metalness={solidMetalness}
          wireframe={isWireframe}
          transparent={styleConfig.transparent}
          opacity={styleConfig.opacity}
          polygonOffset={showEdges}
          polygonOffsetFactor={1}
          polygonOffsetUnits={1}
          depthWrite={!styleConfig.transparent}
        />
      </mesh>

      {/* AutoCAD Feature Edge Lines (Signature CAD contour lines) */}
      {showEdges && edgesGeo && (
        <lineSegments geometry={edgesGeo} renderOrder={1}>
          <lineBasicMaterial
            color={edgeColor}
            linewidth={1.5}
            transparent={styleConfig.transparent}
            opacity={isXRay ? 0.75 : 1.0}
          />
        </lineSegments>
      )}
    </group>
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
      // AutoCAD Standard SE Isometric default
      camera.position.set(dist * 0.85, dist * 0.75, dist * 0.85);
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
    visualStyle = 'shaded_edges',
    backgroundTheme = 'autocad_dark',
    materialType = 'cad_gray',
    showAxes = true,
    showGrid = true,
    showDimensions = true,
    onCoordsUpdate,
  },
  ref
) {
  const [loadedGeometry, setLoadedGeometry] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const cameraCtrlRef = useRef(null);

  useImperativeHandle(ref, () => ({
    resetView: () => cameraCtrlRef.current?.resetView(),
    setCameraView: (type) => cameraCtrlRef.current?.setCameraView(type)
  }));

  const bgConfig = VIEWPORT_BACKGROUNDS[backgroundTheme] || VIEWPORT_BACKGROUNDS.autocad_dark;

  const fullUrl = resolveAssetUrl(meshUrl);
  const handleGeometryLoaded = useCallback((geometry) => {
    setLoadError(null);
    setLoadedGeometry(geometry);
  }, []);
  const handleLoadError = useCallback((error) => {
    setLoadedGeometry(null);
    setLoadError(error);
  }, []);

  useEffect(() => {
    setLoadError(null);
    setLoadedGeometry(null);
  }, [fullUrl]);

  return (
    <Canvas
      className="viewer-canvas"
      shadows={{ type: THREE.PCFShadowMap }}
      camera={{ position: [85, 65, 85], fov: 45 }}
      gl={{ antialias: true, alpha: true, preserveDrawingBuffer: true }}
      onPointerMove={(e) => {
        if (onCoordsUpdate && e.point) {
          onCoordsUpdate({
            x: e.point.x.toFixed(1),
            y: e.point.y.toFixed(1),
            z: e.point.z.toFixed(1),
          });
        }
      }}
    >
      {/* Studio CAD Lighting: Key + Counter Fill + Ground Bounce */}
      <ambientLight intensity={0.5} />
      <directionalLight
        position={[90, 140, 90]}
        intensity={1.75}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-bias={-0.0001}
      />
      <directionalLight position={[-70, 60, -70]} intensity={0.75} color="#CBD5E1" />
      <directionalLight position={[0, -70, 0]} intensity={0.35} color="#94A3B8" />

      {/* AutoCAD Precision Millimeter Grid */}
      {showGrid && (
        <Grid
          position={[0, -0.01, 0]}
          args={[300, 300]}
          cellSize={5}
          cellThickness={1.0}
          cellColor={bgConfig.gridCellColor}
          sectionSize={25}
          sectionThickness={1.8}
          sectionColor={bgConfig.gridSectionColor}
          fadeDistance={300}
          fadeStrength={1.1}
          infiniteGrid
        />
      )}

      {/* AutoCAD Red/Green Origin Axes */}
      <AutoCADOriginAxes length={150} visible={showAxes} />

      {/* 3D Model + Feature Edge Lines + Dimension Badges */}
      {loadError && (
        <Html center>
          <div className="viewer-load-error" role="alert">
            <strong>Model preview unavailable</strong>
            <span>Check that the backend is running and generate the part again.</span>
          </div>
        </Html>
      )}
      {fullUrl && (
        <Suspense fallback={null}>
          <Center>
            <STLMesh
              url={fullUrl}
              onError={handleLoadError}
              onGeometryLoaded={handleGeometryLoaded}
              visualStyle={visualStyle}
              materialType={materialType}
            />
            <DimensionBoundingBox geometry={loadedGeometry} visible={showDimensions} />
          </Center>
          <CameraController ref={cameraCtrlRef} loadedGeometry={loadedGeometry} />
        </Suspense>
      )}

      {/* Interactive AutoCAD ViewCube in Top-Right */}
      <GizmoHelper alignment="top-right" margin={[70, 70]}>
        <GizmoViewcube
          textColor="#0F172A"
          strokeColor="#64748B"
          color="#CBD5E1"
          hoverColor="#00A4EF"
        />
      </GizmoHelper>

      {/* AutoCAD WCS/UCS 3D Coordinate Tripod in Bottom-Left */}
      {showAxes && (
        <GizmoHelper alignment="bottom-left" margin={[60, 60]}>
          <GizmoViewport
            axisColors={['#EF4444', '#22C55E', '#3B82F6']}
            labelColor="#FFFFFF"
            labels={['X', 'Y', 'Z']}
            axisHeadScale={1.1}
          />
        </GizmoHelper>
      )}

      {/* Orbit Controls with Smooth CAD Damping — full 3-axis freedom */}
      <OrbitControls
        enableDamping
        dampingFactor={0.08}
        screenSpacePanning={true}
        minDistance={1}
        maxDistance={5000}
        minPolarAngle={0}
        maxPolarAngle={Math.PI}
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        makeDefault
      />
    </Canvas>
  );
});

export default Viewer3D;
