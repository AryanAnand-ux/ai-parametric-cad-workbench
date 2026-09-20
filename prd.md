# Product Requirements Document (PRD)
## AI Parametric CAD Workbench

**Version:** 1.0  
**Last Updated:** September 2026  
**Status:** Active Development  

---

## 1. Overview

### 1.1 Product Vision
The AI Parametric CAD Workbench is a browser-based, AI-powered engineering design tool that lets engineers, students, and makers generate, visualize, and iterate on 3D CAD models using natural language prompts — no traditional CAD software knowledge required.

### 1.2 Problem Statement
Traditional parametric CAD tools (SolidWorks, FreeCAD, Fusion 360) have steep learning curves and require significant domain expertise. Engineers waste hours on repetitive geometry definitions when describing a part in plain English takes seconds.

### 1.3 Solution
An LLM-driven pipeline converts a natural language description into a parametric Python script (using the `build123d` CAD library), executes it in a sandboxed environment, and returns an interactive 3D mesh alongside editable parameters — all in the browser within ~10 seconds.

---

## 2. Target Users

| Persona | Description | Primary Need |
|---------|-------------|--------------|
| **Student Engineer** | Undergraduate / grad student learning CAD | Fast prototyping without learning CAD UI |
| **Maker / Hobbyist** | 3D printing enthusiast | Quick model generation for printing |
| **Mechanical Engineer** | Professional using legacy CAD tools | Rapid ideation and concept sketching |
| **Educator** | Teaching parametric design | Demos, interactive examples |
| **Researcher** | Computational geometry / AI-CAD | Benchmark platform, dataset generation |

---

## 3. Core Features

### 3.1 Natural Language → CAD (MVP)
- User types a plain English description (e.g. *"A hollow cylinder 50mm diameter, 80mm tall, 4mm wall"*)
- System generates a `build123d` Python script via multi-tier LLM pipeline
- Script is executed in a sandboxed subprocess
- 3D mesh (GLB/OBJ/STL/STEP) is returned to the browser
- Interactive 3D viewer renders the mesh with orbit, zoom, pan controls

### 3.2 Parametric Editing
- Generated models expose named parameters (e.g. `width`, `height`, `wall_thickness`)
- Users can adjust parameters via sliders or direct value inputs
- Recompute triggers a backend script re-execution with updated values
- Diff between recompute runs is shown (mesh info delta)

### 3.3 Chat-to-Modify
- Users can describe modifications in natural language after generation
- ("Make the flange thicker" / "Add 4 mounting holes")
- LLM rewrites the parametric script to satisfy the modification request
- Modification history is tracked in the chat panel

### 3.4 Multi-Format Export
- Download models in: **STL**, **STEP**, **OBJ**, **GLB**
- STEP format preserves parametric CAD topology
- GLB/OBJ suitable for rendering and game engines

### 3.5 Public Gallery
- Users can share models to a public community gallery
- Gallery browse page with model cards (name, description, thumbnail)
- Direct link sharing with unique model IDs

### 3.6 User Authentication
- JWT-based auth (register / login / guest mode)
- Projects saved to SQLite database per user account
- Version history per project (recompute creates new version)

### 3.7 Onboarding Tour
- Step-by-step interactive guide for first-time users
- Highlights: prompt bar, parameter sliders, viewport controls, export

---

## 4. Non-Functional Requirements

### 4.1 Performance
| Metric | Target |
|--------|--------|
| Generation latency (P50) | 10 seconds |
| Recompute latency (P50) | 3 seconds |
| 3D mesh load time | 2 seconds |
| Frontend first paint | 1.5 seconds |

### 4.2 Reliability
- Rate limiter: 10 req/min generate, 10 req/min modify, 40 req/min recompute (per IP)
- Self-correction loop: up to 3 retries on execution error
- Artifact cleanup: temp files removed after configurable TTL
- Backend availability: 99% uptime target (single-node)

### 4.3 Security
- AST-level sandboxing: all LLM-generated Python scripts validated via `ast.parse` before execution
- Blocked patterns: `subprocess`, `os.system`, `exec()`, `eval()`, `open()` in generated code
- Script ID allowlist: only whitelisted `script_id` values can be recomputed
- JWT tokens expire; admin endpoints require `ADMIN_TOKEN` header

### 4.4 Scalability
- CAD execution concurrency cap: `CAD_MAX_CONCURRENT_EXECUTIONS` (default: 2)
- Execution timeout: `CAD_EXECUTION_TIMEOUT_SECONDS` (default: 60s)
- ChromaDB RAG index: 121-document corpus, fully local (no API quota)

---

## 5. User Journey

```
Landing Page
     |
     v
[Enter App] --> Workbench
                   |
             [Prompt Bar]  <- "Generate a flanged pipe connector..."
                   |
             POST /api/generate
                   |
             [3D Viewer]  <- Interactive mesh rendered
                   |
        [Adjust Params] [Chat Modify] [Export/Share]
        (sliders)    (natural lang)  (STL/STEP/OBJ/GLB)
```

---

## 6. API Contracts

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generate` | POST | Generate new CAD model from prompt |
| `/api/recompute` | POST | Re-run script with updated parameters |
| `/api/modify` | POST | Modify existing model via natural language |
| `/api/health` | GET | Backend health + LLM provider status |
| `/api/export/{script_id}/{format}` | GET | Download model file |
| `/api/projects` | GET/POST | List/create user projects |
| `/api/gallery` | GET | Browse public gallery |
| `/auth/register` | POST | Create account |
| `/auth/login` | POST | Obtain JWT token |

---

## 7. Out of Scope (v1)

- Real-time collaboration / multiplayer sessions
- Cloud-hosted CAD execution (all compute is local/self-hosted)
- Assemblies with motion constraints / simulations
- Plugin marketplace
- Mobile-native app (responsive web only)

---

## 8. Success Metrics

| KPI | Target |
|-----|--------|
| Generation success rate | 85%+ |
| Recompute success rate | 95%+ |
| Test suite pass rate | 33/33 (100%) |
| Benchmark weekly CI pass | 85%+ prompt success |
| User retention (session >5 min) | 40%+ |
