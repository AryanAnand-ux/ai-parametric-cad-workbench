# AI-Driven Parametric CAD Workbench

> **Natural Language → 3D Solid Model.** Type a mechanical part description, get an interactive 3D model in your browser, tune it live with real-time sliders, refine it conversationally with Chat-to-Modify, and export production-ready STL & STEP files.

---

## ⚡ Quick Start (Run Locally in 2 Steps)

### 1. Backend Setup (FastAPI + build123d + RAG)
```bash
# Navigate to backend
cd backend

# Create & activate virtual environment
python -m venv venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (cmd):
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API Keys (Copy .env.example)
copy .env.example .env     # Windows
# cp .env.example .env       # Linux/macOS
```

> **Add your API Key in `.env`:**
> `GEMINI_API_KEY=your_key_here` (Free from [Google AI Studio](https://aistudio.google.com/apikey))  
> `GEMINI_WEB_ENABLED=true` *(optional Gemini Web fallback; anonymous mode works for basic access)*\
> `GROQ_API_KEY=your_key_here` *(optional Groq fallback)*

The backend tries the official Gemini API first, then Gemini Web when enabled, then Groq if configured. For Gemini Web cookie-authenticated access, set `GEMINI_WEB_COOKIE` or `GEMINI_WEB_COOKIE_FILE`; advanced options such as `GEMINI_WEB_AUTH_USER`, `GEMINI_WEB_XSRF_TOKEN`, `GEMINI_WEB_BL`, proxy, retry, and timeout controls are documented in `backend/.env.example`.

Run pre-flight check & start server:
```bash
python startup_check.py
python -m uvicorn main:app --reload --port 8000
```
*Backend runs on: **http://127.0.0.1:8000** | Interactive Swagger Docs: **http://127.0.0.1:8000/docs***

---

### 2. Frontend Setup (React + Vite + Three.js)
Open a new terminal:
```bash
# Navigate to frontend
cd frontend

# Install node dependencies
npm install

# Start Vite dev server
npm run dev
```
*Frontend runs on: **http://localhost:5173***

### Production Docker Setup

Copy `backend/.env.example` to `backend/.env`, add the required LLM key or enable `GEMINI_WEB_ENABLED=true`, and set a strong `ADMIN_TOKEN`. Then run:

```bash
docker compose up --build
```

The frontend is served at **http://localhost** and proxies API/model requests to the backend. Generated artifacts are stored in the persistent `cad-artifacts` volume. `RELOAD=false` is required for production; `ALLOWED_ORIGINS` should contain only trusted frontend origins.

Complex generation and chat-to-modify requests allow up to five minutes by default (`VITE_GENERATION_TIMEOUT_MS=300000`). Fast health and recompute requests use shorter client timeouts.

---

## 🌟 Key System Features

- 🧊 **Real CAD Solid Engine (`build123d` + OpenCASCADE)**: Generates true boundary-representation (B-Rep) solid models with exact CSG operations, fillets, chamfers, and STEP/STL export.
- 📦 **Multi-Format Export Suite (STEP, STL, OBJ, GLB, 3MF)**: Export production STEP boundary representations for CNC/CAM, STL for 3D slicing, Wavefront OBJ for 3D graphics, and GLTF/GLB binary for WebGL & AR.
- 🏛️ **Public Community Gallery (`/api/gallery`, `#gallery`)**: Masonry grid of published designs with live search, engineering tag filters, sort options (recent/popular/most forked), instant fork-to-workspace, and liking.
- 📡 **Structured JSON Telemetry & Observability (`/api/metrics`)**: In-process observability recording request counts, p95 latencies, error percentages, and model success distributions.
- 🤖 **CI/CD Automated Pipelines (`.github/workflows/`)**: Automated GitHub Actions running pytest regression test suites, Vite bundle builds on every PR/push, and scheduled benchmark regression guards.
- 🧩 **Modular Component Architecture & State Machine**: Scalable `useCADWorkbench` reducer hook managing workspace state, with isolated components (`ViewportToolbar`, `PromptPanel`, `TelemetryHUD`, `ErrorBanner`, `ChatModifyPanel`, `CodeInspectorModal`).
- 🧠 **101-Example RAG Vector Store**: Uses local `sentence-transformers/all-MiniLM-L6-v2` embeddings in ChromaDB to retrieve top-3 CAD code examples for few-shot LLM prompt injection across multiple engineering domains.
- ⚡ **Real-Time SSE Generation Pipeline (`POST /api/generate/stream`)**: Server-Sent Events stream live progress across 5 discrete pipeline stages (Blueprint Retrieval → Parametric Synthesis → AST Audit → Kernel Compilation → Topology Check) with sub-second feedback.
- 💬 **Chat-to-Modify (`POST /api/modify`)**: Conversationally refine generated models with natural language (e.g., *"Make the walls 2mm thicker"*, *"Add 4x M3 mounting holes"*) without losing parameter continuity. Creates versioned scripts (`_v1`, `_v2`...).
- ⚡ **Sub-200ms Parametric Recomputation**: Adjusting UI sliders recomputes solid geometry directly via `build123d` in real-time without invoking LLM tokens.
- 🗄️ **Multi-Tenant Workspaces & Persistence**: SQLAlchemy async ORM (SQLite / PostgreSQL) managing persistent user accounts, design histories, parameter snapshots, and version trees.
- 🔐 **JWT Authentication & Security**: Secure user registration and login with native `bcrypt` password hashing, token validation, and workspace isolation.
- 🌐 **Virality & Sharing**: Generate public permalinks (`/#model={id}`) and embeddable `<iframe>` 3D CAD viewers to integrate live interactive models into technical documentation.
- 💡 **Guided Onboarding Tour**: 5-step interactive studio walkthrough highlighting natural language synthesis, viewport navigation, sliders, modifications, and CAD exports.
- 📊 **20-Prompt Benchmark Harness**: `backend/benchmark_eval.py` evaluates diverse mechanical engineering parts and records latency, model, self-correction, and geometry metrics in `benchmark_results.json`.
- 💻 **Python Code Inspector**: View, inspect, and copy the raw `build123d` Python script generated by the LLM for any design.
- 🛡️ **AST Security Sandbox**: Whitelists safe modules (`build123d`, `math`, `typing`, etc.), blocks dangerous builtins (`__globals__`, `open`, `eval`, `exec`), and isolates subprocess execution in a non-blocking thread pool.
- 🎨 **Parisian Atelier Design System**: Luxury aesthetic inspired by The Studio by Julie Granger — Espresso (`#474040`), Buttercream (`#FFFDE2`), Warm Sand (`#F6F6F0`), and Forest Green (`#489235`) with `Newsreader` italic serif typography, ViewCube camera navigation, and PBR finishes.
- 🔄 **Automated Self-Correction Loop**: Catches script syntax errors, runtime failures, and non-watertight mesh topology at runtime, feeding tracebacks back to the LLM (up to 3 retries) for autonomous code repair.

---

## 📊 Benchmark Results (Phase 5 Quantitative Evaluation)

| Metric | Result | Benchmark Target |
|---|:---:|:---:|
| **Benchmark prompts** | **20** | Defined in `backend/benchmark_eval.py` |
| **Recorded outputs** | `benchmark_results.json` | Generated by a benchmark run |
| **Scored fields** | Success, first pass, latency, model, volume | Per prompt |

---

## 📁 Repository Structure

```
ai-parametric-cad-workbench/
├── README.md                 ← Project Documentation & Setup Guide
├── WEEKLY_PLAN.md            ← Master Plan & Milestone Roadmap
├── .github/workflows/
│   ├── ci.yml                ← Pytest Backend Suite & Vite Frontend Bundle CI
│   └── benchmark.yml         ← Weekly Automated 20-Prompt Benchmark Regression Guard
├── scripts/
│   └── clean_artifacts.py    ← Standalone CAD Artifact Lifecycle Maintenance
├── backend/
│   ├── main.py               ← FastAPI Application, Route Handlers, SSE Streaming (/generate/stream)
│   ├── database.py           ← Async SQLAlchemy Engine & Session Lifecycle (SQLite/PostgreSQL)
│   ├── schemas.py            ← Pydantic V2 API Schemas with String Length Bounds
│   ├── config.py             ← Isolated Directory Configuration & DLL Search Paths
│   ├── startup_check.py      ← Pre-flight Dependency & Vector Index Sanity Check
│   ├── benchmark_eval.py     ← Benchmark Runner & Telemetry Suite (httpx-based)
│   ├── run_tests.py          ← Cross-Platform Unified Pytest Runner
│   ├── pytest.ini            ← Pytest Test Runner Configuration
│   ├── requirements.txt      ← Python Dependencies (build123d, chromadb, fastapi, sqlalchemy, bcrypt, etc.)
│   ├── middleware/
│   │   └── telemetry.py      ← Structured JSON Request Telemetry & In-Memory Metrics Store
│   ├── models/
│   │   ├── __init__.py       ← Central Declarative Base & Table Registry
│   │   ├── user.py           ← User Model (Credentials, Tiers, API Keys)
│   │   └── project.py        ← Workspaces, Generations, & Version History Models
│   ├── routes/
│   │   ├── auth.py           ← User Registration, Login, Token Refresh, & Profile
│   │   ├── projects.py       ← Workspace & Design Persistence CRUD Endpoints
│   │   └── gallery.py        ← Public Design Gallery, Publish, Like, & Fork Endpoints
│   ├── services/
│   │   ├── auth_service.py   ← JWT Creation/Verification & Native Bcrypt Password Hashing
│   │   ├── cad_runner.py     ← Subprocess Executor, AST Sandbox, Multiformat Export (STL, STEP, OBJ, GLB)
│   │   ├── prompts.py        ← 15 Strict CAD Code Rules, System Prompts, & RAG Templates
│   │   ├── rag_service.py    ← ChromaDB Indexing, SentenceTransformers Embedding, & Retrieval
│   │   ├── llm_service.py    ← Gemini API, Gemini Web, and Groq Fallback Chain & Self-Correction
│   │   ├── gemini_web_client.py ← In-Process Gemini Web StreamGenerate Client
│   │   └── cleanup.py        ← Temporary CAD Artifact Lifecycle Manager
│   ├── test_api.py           ← Integration Tests for All Routes
│   ├── test_auth_projects.py ← Multi-Tenant Auth & Workspace Isolation Integration Tests
│   ├── test_gallery_and_formats.py ← Public Gallery, Telemetry Metrics, & Multi-Format Tests
│   ├── test_ast_security.py  ← AST Sandbox Security Test Suite (7 tests)
│   ├── test_geometry_validation.py ← Topology & Watertightness Verification Test Suite
│   ├── test_recompute_validation.py ← Fast Slider Recomputation Contract Test Suite
│   ├── test_modify_params.py ← Chat-to-Modify Schema & Contract Test Suite
│   └── rag_corpus/
│       ├── examples_week4.py ← Basic CAD Snippets (plates, brackets, tubes)
│       ├── examples_week5.py ← Mechanical CAD Snippets (couplings, pulleys, gears)
│       ├── examples_week8.py ← Multi-Body Parts (chassis, deadcat drone arms)
│       ├── examples_engineering.py ← High-Tolerance Industrial & Aerospace Parts
│       └── examples_complex.py ← High-Difficulty Engineering & Mechanical CAD Examples
└── frontend/
    ├── index.html            ← Main HTML Template with Google Fonts (Newsreader, Open Sans, JetBrains Mono)
    ├── vite.config.js        ← Vite Config with Backend Proxy & Vendor Chunk Splitting
    ├── package.json          ← Frontend Dependencies (@react-three/fiber, drei, three, axios)
    └── src/
        ├── Router.jsx        ← Client-Side Hash Router with React.lazy Code Splitting (#app, #gallery)
        ├── LandingPage.jsx   ← Interactive Atelier Engineering Landing Page with 3D Showcase & Memberships
        ├── App.jsx           ← CAD Workbench Studio Shell
        ├── index.css         ← Parisian Atelier Luxury Design System (Espresso, Buttercream, Warm Sand)
        ├── api.js            ← Axios Client with SSE Streaming Reader, Auth Interceptors, & Timeouts
        ├── pages/
        │   └── Gallery.jsx   ← Public CAD Community Gallery (Masonry Grid, Search, Tag Filters, Forking)
        ├── hooks/
        │   ├── useAuth.js         ← Reactive Authentication & Workspace Session Hook
        │   └── useCADWorkbench.js ← Scalable Workbench Reducer State Machine (30+ States Centralized)
        └── components/
            ├── Viewer3D.jsx           ← React Three Fiber WebGL Viewer (PBR Presets, Dimension Annotations)
            ├── ViewportToolbar.jsx    ← Floating 3D Controls (Visual Style, Camera Angle, Material, Formats)
            ├── PromptPanel.jsx        ← Natural Language Prompt Input with Quick Launch Presets
            ├── TelemetryHUD.jsx       ← B-Rep Envelope, Volume, and Watertight Manifold Metrics
            ├── ChatModifyPanel.jsx    ← Conversational CAD Delta Refinement Panel
            ├── CodeInspectorModal.jsx ← Python CAD Script Inspector & Clipboard Copier
            ├── ErrorBanner.jsx        ← Unified Dismissible Error Notification Bar
            ├── ParameterSlider.jsx    ← Parametric Slider Control with Unit Detection & Steppers
            ├── AuthModal.jsx          ← Studio Sign-In & Registration Modal
            ├── GenerationProgress.jsx ← 5-Stage Real-Time Pipeline Progress Visualizer Card
            ├── ProjectSidebar.jsx     ← Workspace Slide-Out Drawer with Saved CAD Design Trees
            ├── OnboardingTour.jsx     ← 5-Step Guided Spotlight Walkthrough
            └── ShareModal.jsx         ← Public Permalinks, 3D Embeds, & Publish to Gallery Modal
```

---

## 🔌 API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status, storage readiness, & LLM configuration |
| `GET` | `/api/metrics` | **Telemetry & Observability:** Real-time request counts, error rates, p95 latencies |
| `POST` | `/api/generate` | **Primary:** NL prompt → RAG (101 examples) → LLM → execute → 3D solid *(Rate limited)* |
| `POST` | `/api/generate/stream` | **Real-Time Streaming:** Server-Sent Events (SSE) streaming 5-stage synthesis pipeline |
| `POST` | `/api/modify` | **Chat-to-Modify:** Refine existing script via natural language prompt *(Rate limited)* |
| `POST` | `/api/recompute` | Fast parametric slider recomputation (sub-200ms, no LLM call) *(Rate limited)* |
| `GET` | `/api/gallery` | **Public Gallery:** Paginated community designs with search, tag filters, & sorting |
| `POST` | `/api/gallery/{id}/publish` | Publish private design to the public community gallery |
| `POST` | `/api/gallery/{id}/like` | Increment community like count on a public design |
| `POST` | `/api/gallery/{id}/fork` | Fork public community design directly into personal private workspace |
| `POST` | `/api/auth/register` | Register new CAD Atelier user account (bcrypt password hashing) |
| `POST` | `/api/auth/login` | Authenticate user & issue JWT Bearer access token |
| `POST` | `/api/auth/refresh` | Refresh expired JWT session token |
| `GET` | `/api/auth/me` | Fetch authenticated user profile, tier, and workspace metadata |
| `GET` | `/api/projects` | List all private workspaces for authenticated user |
| `POST` | `/api/projects` | Create a new isolated design workspace |
| `GET` | `/api/projects/{id}` | Retrieve project details and associated generations |
| `DELETE` | `/api/projects/{id}` | Delete workspace and associated design records |
| `GET` | `/api/generations/{id}` | Retrieve full generation record with parameter state and versions |
| `GET` | `/api/script/{id}` | Retrieve raw generated `build123d` Python script by ID *(Requires admin token in production)* |
| `GET` | `/api/admin/models` | List all stored 3D STL/STEP model artifacts *(Requires admin token)* |
| `POST` | `/api/admin/cleanup` | Remove temporary artifacts older than threshold *(Requires admin token)* |
| `GET` | `/api/download/{id}/{fmt}` | Direct attachment download (`fmt=stl\|step\|stp\|obj\|glb`) |
| `GET` | `/static/models/{file}` | Serve generated STL, STEP, OBJ, and GLB files *(Python source requires admin token)* |

The admin cleanup, model listing, and source-code routes accept the `X-Admin-Token` header when `ADMIN_TOKEN` is configured. Production mode (`ENVIRONMENT=production`) refuses to start protected operations without that token. STL/STEP/OBJ/GLB downloads and previews remain public for browser rendering; generated Python source strictly requires the admin token. The AST validator and stripped environment variables (`PYTHONNOUSERSITE=1`, `PYTHONPATH=""`) form a layered defense; production deployments should use container boundaries and restricted network access.

---

## 🧪 Running Automated Tests & Benchmark

```bash
# 1. Run all unit, regression, and security tests via unified runner
cd backend
.\venv\Scripts\python run_tests.py

# 2. Run CAD Engine & RAG Retrieval Integration Tests
.\venv\Scripts\python test_week4_build123d.py

# 3. Run FastAPI Endpoint Verification
.\venv\Scripts\python test_api.py

# 4. Run Frontend Production Bundle Build
cd ../frontend
npm run build
```

---

## 👥 Team & Responsibilities

| Member | Primary Focus & Deliverables |
|---|---|
| **Member 1 (Aryan Anand)** | Full Pipeline Architecture, LLM Multi-Model Orchestrator, AST Security Sandbox, FastAPI Backend, 15 Strict CAD Rules |
| **Member 2** | ChromaDB Vector Store & Local Embeddings (SentenceTransformers), 101-Example RAG Corpus Engineering, Geometry Topology Validation |
| **Member 3** | React 19 Frontend Architecture, React Three Fiber 3D WebGL Canvas, Parisian Atelier Luxury UI, Real-Time Parametric Sliders, Workspaces & Tour |
