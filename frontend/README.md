# AI Parametric CAD Workbench — Frontend

A Technical Neobrutalist WebGL user interface for natural language 3D CAD modeling, live parametric recomputation, and conversational engineering adjustments.

---

## 🚀 Tech Stack

- **React 19** + **Vite 8** (Fast HMR & Optimized Bundling)
- **Three.js** + **@react-three/fiber** + **@react-three/drei** (3D WebGL Canvas)
- **Axios** (API Client with 180s self-correction timeout)
- **Design System**: Technical Neobrutalist Bento Grid (2.5px solid outlines, hard 4px drop-shadows, Space Grotesk typography)

---

## 📦 Key Components

| Component | Path | Description |
|---|---|---|
| `App.jsx` | `src/App.jsx` | Bento Grid shell, prompt inputs, Chat-to-Modify panel, and state management |
| `Viewer3D.jsx` | `src/components/Viewer3D.jsx` | R3F 3D Canvas, STLLoader, OrbitControls, 4 PBR materials, 3D Bounding Box Annotations |
| `ParameterSlider.jsx` | `src/components/ParameterSlider.jsx` | Parametric dimension sliders with unit detection, `+`/`-` steppers, and reset buttons |
| `api.js` | `src/api.js` | Axios API client targeting `/api/generate`, `/api/modify`, `/api/recompute`, and `/api/health` |

---

## 🛠️ Development Setup

```bash
# Install dependencies
npm install

# Start local development server (proxies to http://localhost:8000)
npm run dev

# Build production bundle
npm run build
```

