# Week 5 — RAG Corpus Expansion (50 Examples) & React Three Fiber Frontend

> **One-line goal:** Scale the verified CAD vector corpus from 20 to 50 industrial reference examples to eliminate advanced geometry hallucinations, and construct a GPU-accelerated React 18 + Vite + Three.js WebGL viewport with dynamic camera auto-framing and parametric slider controls.

---

## 1. Framing & Architecture Overview

By Week 4, the core backend pipeline — OpenCASCADE solid execution, AST security sandbox, and ChromaDB vector retrieval — was functional. However, two major hurdles remained:

1. **Corpus Coverage Limitations:** 20 baseline examples covered simple geometric primitives, but the LLM still struggled with common mechanical engineering patterns: Pitch Circle Diameter (PCD) bolt circles, thin-walled enclosures, shaft keyways, cable channels, and servo mounts.
2. **Lack of User Interface:** Generated `.stl` files could only be validated via terminal scripts or external CAD viewers. Users needed an interactive, browser-native 3D workbench.

Week 5 solved both challenges: scaling the RAG corpus to 50 verified examples in `rag_corpus/examples_week5.py` and scaffolding the complete React 18 frontend with React Three Fiber (`@react-three/fiber` + `@react-three/drei`).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        React 18 + Vite Frontend                        │
│                                                                        │
│  ┌───────────────────────┐         ┌─────────────────────────────────┐ │
│  │   Natural Language    │         │      Three.js WebGL Canvas      │ │
│  │     Prompt Input      │         │   (Viewer3D.jsx + STLLoader)    │ │
│  └───────────┬───────────┘         │                                 │ │
│              │ POST /api/generate  │ • OrbitControls (pan/zoom/orbit)│ │
│              ▼                     │ • Auto-framing via Bounding     │ │
│  ┌───────────────────────┐         │   Sphere Trigonometry           │ │
│  │  Parameter Sliders    │         │ • Solid / Wireframe toggle      │ │
│  │ (ParameterSlider.jsx) │         │ • Studio blueprint grid floor   │ │
│  │ • Range normalization │         └─────────────────────────────────┘ │
│  │ • Unit detection (mm/°)│                          ▲                  │
│  │ • ↺ Reset to default  │                          │                  │
│  └───────────────────────┘                          │ GET /static/stl  │
└─────────────────────────────────────────────────────┼──────────────────┘
                                                      │
┌─────────────────────────────────────────────────────▼──────────────────┐
│                      ChromaDB 50-Example Corpus                        │
│  • 20 Baseline Primitives (Week 4)                                     │
│  • 30 Advanced Mechanical Assemblies (Week 5):                         │
│    - PCD Circular Bolt Flanges    - Thin-wall Electronics Enclosures   │
│    - Keyway Shaft Collars         - Pulley V-Grooves & C-Channels      │
│    - Servo Mounts & Standoffs     - Hinges with Barrel & Pin           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. What Was Built

### 2.1 RAG Corpus Scaling to 50 Verified Examples (`rag_corpus/examples_week5.py`)

Authored and validated 30 advanced mechanical component pairs, expanding the ChromaDB index to 50 total canonical references:

1. **Rotational & Flanged Parts:**
   - Circular pipe flange with 4/6/8-hole PCD bolt circles (`PolarLocations` / trigonometric arrays).
   - Shaft collar with radial set screw hole.
   - Stepped pulley with V-belt trapezoidal groove.
   - Spur gear blank with shaft bore and keyway slot.
2. **Structural & Mounting Elements:**
   - Thin-walled electronics project box with lid rim.
   - Heavy-duty U-bracket with slotted mounting holes.
   - C-channel and T-slot extrusion profile cover.
   - Cantilever I-beam with reinforcement gussets.
   - Drill jig bushing with press-fit collar.
3. **Robotics & Mechatronics Hardware:**
   - NEMA 17 / 9g micro servo motor mounting bracket.
   - Electronic Speed Controller (ESC) tray.
   - 18650 cylindrical battery holder cradle.
   - PCB standoff matrix with M3 clearance holes.
   - Articulated cable chain link with snap-fit pivot.
   - Robot gripper finger with grip ridges.

> **Corpus Validation Policy:** Every snippet in `examples_week5.py` was executed through `cad_runner.py` and inspected with `trimesh` to verify that it exports a single, non-empty, watertight manifold solid with positive volume before indexation.

### 2.2 WebGL 3D Viewer (`frontend/src/components/Viewer3D.jsx`)

Built a hardware-accelerated 3D viewport using Three.js and React Three Fiber:

- **Asynchronous STL Loading:** Uses Three.js `STLLoader` to stream binary and ASCII STL models directly from the backend `/static/models/` URL.
- **OrbitControls:** Intuitive camera interaction (left-click drag to rotate, scroll to zoom, right-click drag to pan).
- **GPU Memory Management:** Explicitly disposes of old geometry instances (`geoRef.current.dispose()`) when a new model or parameter recomputation is loaded, preventing WebGL memory leaks during active slider manipulation.
- **Render Modes:** Toggleable Solid (PBR metallic blue shader) and Wireframe mode.
- **Studio Blueprint Environment:** Blueprint grid floor with infinite ground plane, ambient lighting, directional fill lights, and soft shadow mapping (`castShadow`, `receiveShadow`).

### 2.3 Mathematical Camera Auto-Framing (`CameraController`)

Because generated CAD models range in scale from a 5mm fastener to a 500mm drone chassis, fixed camera coordinates either cause clipping or render tiny, invisible parts.

We implemented an auto-framing controller using bounding sphere trigonometry:

```javascript
const CameraController = forwardRef(function CameraController({ loadedGeometry }, ref) {
  const { camera, controls } = useThree();

  const resetCamera = () => {
    if (!loadedGeometry) return;
    loadedGeometry.computeBoundingSphere();
    const sphere = loadedGeometry.boundingSphere;
    if (!sphere || sphere.radius <= 0) return;

    // Calculate required distance based on camera vertical field of view (FOV)
    const dist = Math.max(sphere.radius * 2.8, 15);
    camera.position.set(dist, dist * 0.6, dist);
    camera.lookAt(sphere.center);
    
    if (controls) controls.target.copy(sphere.center);
    camera.near = Math.max(0.1, dist * 0.01);
    camera.far = dist * 100;
    camera.updateProjectionMatrix();
  };

  useEffect(() => {
    resetCamera();
  }, [loadedGeometry]);

  return null;
});
```

### 2.4 Dynamic Parametric Controls (`frontend/src/components/ParameterSlider.jsx`)

Built reusable UI slider controls dynamically rendered from the `CADParameter` array:

- **Unit Formatting:** Smart unit detection automatically appends `' mm'` for linear dimensions, `'°'` for angular parameters, and unitless integers for discrete counts (`num_bolts`, `ribs`).
- **Normalized Track Fill:** Calculates percentage width (`((value - min) / (max - min)) * 100`) to render a smooth CSS gradient fill along the slider track.
- **Default Reset (↺):** One-click button to restore modified parameters back to their original default value.
- **Step Precision Formatting:** Dynamically rounds numerical displays to match step granularity (e.g. `0.5` -> 1 decimal place; `1` -> integer).

---

## 3. Technology Used

| Layer | Technology | Role |
|---|---|---|
| Frontend Build Tool | **Vite 5+** | Rapid bundling and Hot Module Replacement (HMR) |
| UI Framework | **React 18** | Declarative state management and component lifecycle |
| 3D Graphics Engine | **Three.js** | WebGL canvas rendering |
| 3D React Binding | **@react-three/fiber** | Declarative Three.js scene graph management |
| 3D Helpers | **@react-three/drei** | `OrbitControls`, `Grid`, `Center` helpers |
| Mesh Loader | **three/STLLoader** | Binary/ASCII STL parser |
| RAG Embeddings | **sentence-transformers** | Embedding 30 new snippets (`all-MiniLM-L6-v2`) |

---

## 4. Key Problems Solved (with Technical Details)

### Problem 1: WebGL Memory Leaks on Frequent Model Updates

**Root Cause:** In Three.js, simply replacing a mesh geometry in React state does not free GPU buffer allocations (VBOs), causing browser tab memory to balloon over time.

**Solution:** In `Viewer3D.jsx`, a `geoRef` tracks active buffer geometries. When `url` changes or the component unmounts, `geoRef.current.dispose()` is explicitly invoked, ensuring GPU memory is garbage-collected cleanly.

```javascript
useEffect(() => {
  if (!url) return;
  const loader = new STLLoader();
  loader.load(url, (geo) => {
    geo.computeVertexNormals();
    geo.center();
    if (geoRef.current) geoRef.current.dispose();
    geoRef.current = geo;
    setGeometry(geo);
    if (onGeometryLoaded) onGeometryLoaded(geo);
  });

  return () => {
    if (geoRef.current) {
      geoRef.current.dispose();
      geoRef.current = null;
    }
  };
}, [url]);
```

### Problem 2: Camera Clipping on Variable Part Scales

**Root Cause:** A 400mm chassis extends past the camera's default clipping plane (`far`), while a 10mm bolt is dwarfed by distant perspectives.

**Solution:** Dynamic bounding sphere calculation in `CameraController` automatically recalculates `camera.near`, `camera.far`, `camera.position`, and `controls.target` on every geometry load event.

---

## 5. Files Created / Modified

| File | Location | Description |
|---|---|---|
| `examples_week5.py` | `backend/rag_corpus/examples_week5.py` | 30 verified build123d mechanical engineering snippets |
| `App.jsx` | `frontend/src/App.jsx` | Main application shell, prompt input, state coordination |
| `Viewer3D.jsx` | `frontend/src/components/Viewer3D.jsx` | Three.js WebGL viewer, auto-framing, OrbitControls, shadows |
| `ParameterSlider.jsx` | `frontend/src/components/ParameterSlider.jsx` | Dynamic slider component with unit detection and reset |
| `vite.config.js` | `frontend/vite.config.js` | Dev server proxy configuration (`/api` -> backend `:8000`) |

---

## 6. What Was Missing / Improved in Subsequent Weeks

1. **Slider Debounce & Fast Recompute Endpoint (Addressed in Week 6):**
   - In Week 5, dragging sliders did not yet trigger fast parameter recomputation without calling the LLM.
   - *Fix:* In Week 6, `/api/recompute` was added with 100ms slider debouncing, enabling sub-second parametric mesh updates without LLM involvement.

2. **UI Visual Polish & Neobrutalism System (Addressed in Week 7):**
   - The initial Week 5 UI used basic HTML form styling.
   - *Fix:* Redesigned in Week 7 using a Soft Neobrutalism design system (high-contrast 2.5px borders, offset shadows, Space Grotesk typography).

3. **Chat-to-Modify Panel (Addressed in Week 7):**
   - Week 5 only supported initial prompt generation.
   - *Fix:* Added interactive natural language script modification drawer (`/api/modify`).

---

## 7. Exit Criteria vs. Actual Result

| Criterion | Target | Actual |
|---|---|---|
| RAG corpus expanded to 50 examples | ✅ | ✅ 50 verified snippets indexed in ChromaDB |
| React 18 + Vite development server running | ✅ | ✅ Fast HMR on port 5173 with API proxy |
| Three.js STL loading & rendering | ✅ | ✅ STLLoader renders generated solids in WebGL |
| Interactive OrbitControls | ✅ | ✅ Pan, zoom, and rotate around part center |
| Camera auto-framing on all geometry sizes | ✅ | ✅ Bounding sphere auto-fit tested from 10mm to 400mm parts |
| Dynamic parameter sliders rendered | ✅ | ✅ Sliders dynamically generated from response JSON |
