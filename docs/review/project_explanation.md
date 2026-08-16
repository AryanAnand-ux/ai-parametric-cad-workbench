# 🏗️ AI-Driven Parametric CAD Workbench — Master Project Explanation

> **One sentence:** Type a plain English description → get a real, manufacturable 3D solid model in your browser → tune it live with sliders → export for 3D printing or CNC.

---

## 🎯 What This Project Does

This is a **full-stack AI engineering application** that bridges two worlds that have never been connected before at this level:

1. **Natural Language** — what humans speak
2. **Parametric CAD** — what factories understand

Most 3D modeling tools require years of training (Fusion 360, SolidWorks, CATIA). This project makes it possible to generate a structurally valid, dimensionally correct, manufacturable 3D part by just describing it in English — in under 10 seconds.

### The Complete User Journey

```
User types:  "A drone frame with 4 motor arms, 30.5mm FC stack, 6mm motor bolts"
                              ↓
System retrieves:  3 similar build123d code examples from vector DB
                              ↓
AI writes:   Executable Python CAD code following 15 engineering rules
                              ↓
Runner executes: Real OpenCASCADE geometry kernel via build123d
                              ↓
Validator checks: 1 solid body? Watertight? Volume > 0? Dimensions sane?
                              ↓
Browser renders: Interactive 3D model with auto-generated sliders
                              ↓
User refines: Drag slider → model recomputes
              Or type: "Make the arms 20mm longer" → Chat-to-Modify
                              ↓
User downloads: Production-grade STL (3D print) or STEP (CNC / Fusion 360)
```

---

## 🧱 Technology Stack

### Backend (Python)

| Component | Technology | Purpose |
|---|---|---|
| Web Framework | **FastAPI** | Async HTTP, Pydantic validation, auto Swagger docs |
| CAD Engine | **build123d + OpenCASCADE** | Real B-Rep solids with true STEP export |
| LLM Primary | **Gemini 2.5 Flash** | JSON-mode code generation |
| LLM Fallback 2 | **Gemini 3.7 Flash** | Backup when tier 1 fails |
| LLM Fallback 3 | **Gemini Flash Latest** | Third option |
| LLM Fallback 4 | **Groq Llama-3.3-70B** | Ultra-fast inference fallback |
| Vector DB | **ChromaDB** | Local persistent semantic search |
| Embeddings | **all-MiniLM-L6-v2** | Local, offline-capable, 384-dim vectors |
| Mesh Validation | **trimesh** | Watertight check, body count, volume |
| Security | Python **ast** module | Whitelist import sandbox |
| Async Exec | **asyncio.to_thread + subprocess.run** | Non-blocking on Windows |

### Frontend (JavaScript)

| Component | Technology | Purpose |
|---|---|---|
| Framework | **React 18 + Vite** | HMR dev server, component-based UI |
| 3D Renderer | **Three.js + React Three Fiber** | WebGL GPU-accelerated 3D |
| 3D Controls | **@react-three/drei** | OrbitControls, environment maps |
| HTTP Client | **Axios** | Backend API communication |
| Design System | **Vanilla CSS** | Soft Neobrutalism: 2.5px borders, Space Grotesk |

---

## 🗂️ Complete File Structure

```
ai-parametric-cad-workbench/
│
├── README.md
├── WEEKLY_PLAN.md
│
├── backend/
│   ├── main.py                  API routes: /generate /modify /recompute /health
│   ├── schemas.py               Pydantic models
│   ├── config.py                Env vars, paths
│   ├── startup_check.py         Pre-flight checks
│   ├── benchmark_eval.py        20-prompt accuracy benchmark
│   │
│   ├── services/
│   │   ├── llm_service.py       4-tier LLM orchestrator + JSON parser
│   │   ├── prompts.py           System prompt (15 engineering rules + CSG templates)
│   │   ├── cad_runner.py        Subprocess executor + AST sandbox + trimesh validator
│   │   ├── rag_service.py       ChromaDB: index, embed, retrieve, format
│   │   └── cleanup.py           Artifact lifecycle manager
│   │
│   ├── rag_corpus/
│   │   ├── examples_week4.py    20 snippet pairs
│   │   ├── examples_week5.py    30 snippet pairs
│   │   └── examples_week8.py    3 gold-standard examples (chassis, drone, rotation ref)
│   │
│   └── scripts/
│       └── add_rag_examples.py
│
└── frontend/
    ├── vite.config.js           /api proxy → backend
    └── src/
        ├── App.jsx              Main shell, state, chat panel, preset chips
        ├── index.css            Neobrutalism design system
        ├── api.js               Axios client
        └── components/
            ├── Viewer3D.jsx     Three.js canvas, auto-frame, wireframe, shadows
            └── ParameterSlider.jsx  Slider with unit detection, reset, % fill
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Status, storage, API key config |
| `POST` | `/api/generate` | NL → RAG → LLM → build123d → STL + STEP |
| `POST` | `/api/modify` | Chat-to-Modify: refine script via NL |
| `POST` | `/api/recompute` | Fast slider recompute (no LLM call) |
| `GET` | `/api/script/{id}` | Retrieve raw generated Python script |
| `GET` | `/static/models/*.stl` | Serve generated STL to Three.js |
| `GET` | `/static/models/*.step` | Serve STEP file for download |

---

## 🛡️ The 15-Rule Engineering Quality System

| # | Rule | What It Prevents |
|---|---|---|
| 1 | PARAMS → asserts → geometry → validate → export structure | Unstructured code |
| 2 | ALL dimensions in PARAMS dict | Magic numbers |
| 3 | Assert every parameter before geometry | Negative dimensions |
| 4 | Solid-First CSG (no 1D Lines in sketches) | Disconnected geometry islands |
| 5 | `mirror()` not `sx * coord` | Reversed polygon winding |
| 6 | ISO tolerance system (M3=3.4mm) | Undersized/oversized holes |
| 7 | Explicit clearance parameters | Feature collisions |
| 8 | Manufacturing constraints (FDM/CNC/Laser) | Unprintable/unmachinable parts |
| 9 | `int(range(...))` for bolt counts | Float→int crash on slider update |
| 10 | `globals().get('OUTPUT_STL', 'fallback')` | Undefined variable crash |
| 11 | `from build123d import *` only | Blocked imports (os, sys, subprocess) |
| 12 | `Location((x,y,z),(rx,ry,rz))` not `with Rotation()` | TypeError context manager crash |
| 13 | Fillet: `print(warning)` not silent `pass` | Silent fillet failures |
| 14 | Honest comments matching actual geometry | Misleading documentation |
| 15 | `# Units: mm` + coordinate system header | Ambiguous unitless geometry |

---

## 📊 Verified Performance Metrics

| Metric | Measured | Target |
|---|---|---|
| Solid body count (chassis) | **1** (monolithic) | = 1 |
| Watertight (chassis) | **True** | True |
| Volume (chassis) | **192.54 cm³** | > 0 |
| Bounding box (chassis) | **380 × 278 × 4 mm** | Matches spec |
| RAG corpus size | **53 examples** | 50+ |
| RAG top match (chassis query) | **sim = 0.70** | > 0.65 |
| LLM fallback tiers | **4** | ≥ 3 |

---

## 📅 Development Timeline

| Phase | Weeks | Status | Key Deliverable |
|---|---|---|---|
| Foundation | 1–3 | ✅ Complete | FastAPI, subprocess runner, LLM 3-tier, schemas |
| CAD Engine + RAG | 4–5 | ✅ Complete | build123d, ChromaDB 53 examples |
| Full Pipeline | 6–8 | ✅ Complete | End-to-end demo, sliders, Chat-to-Modify, 15-rule validation |
| UI/UX Polish | 9–10 | 🔲 Next | Materials, camera presets, export center, benchmark |
| Testing + Deploy | 11–14 | 🔲 Upcoming | 50-prompt benchmark, deployment, final demo |

---

*See `week1.md` through `week8.md` for deep-dives on each phase.*
