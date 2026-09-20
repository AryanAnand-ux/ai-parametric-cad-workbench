# Architecture Document
## AI Parametric CAD Workbench

**Version:** 1.0  
**Last Updated:** September 2026  

---

## 1. System Overview

The workbench is a full-stack web application with a **FastAPI backend** and **Vite/React frontend**. The core value chain is:

```
User Prompt (NL)
      |
      v
  [LLM Service]  (Gemini / Groq fallback + RAG context)
      |
      v
  [CAD Runner]   (build123d script sandbox execution)
      |
      v
  [Mesh Export]  (trimesh -> STL/STEP/OBJ/GLB)
      |
      v
  [3D Viewer]    (React Three Fiber in browser)
```

---

## 2. Tech Stack

### 2.1 Backend
| Layer | Technology | Version |
|-------|-----------|---------|
| Web framework | FastAPI | >=0.110.0 |
| ASGI server | Uvicorn (standard) | >=0.28.0 |
| Data validation | Pydantic v2 | >=2.6.0 |
| CAD engine | build123d | >=0.8.0 |
| Geometry processing | trimesh + shapely + scipy | Latest |
| ORM / DB driver | SQLAlchemy (async) + aiosqlite | >=2.0.0 |
| Database | SQLite (`cad_workbench.db`) | - |
| Vector store | ChromaDB (persistent, local) | >=0.5.0 |
| Embeddings | sentence-transformers all-MiniLM-L6-v2 | >=3.0.0 |
| Auth | python-jose (JWT) + passlib (bcrypt) | >=3.4.0 |
| LLM API (primary) | google-genai (Gemini) | >=0.1.0 |
| LLM API (fallback) | groq (Llama-3.3-70B) | >=1.0.0 |
| Streaming | sse-starlette | >=2.0.0 |

### 2.2 Frontend
| Layer | Technology | Version |
|-------|-----------|---------|
| Build tool | Vite | Latest |
| UI framework | React 18 | - |
| 3D rendering | React Three Fiber + Three.js | - |
| State management | useReducer (custom hook) | - |
| Styling | Vanilla CSS (index.css) | - |
| HTTP client | fetch (native) | - |
| Routing | Hash-based (`window.location.hash`) | - |

---

## 3. Directory Structure

```
Minor_project/
├── backend/
│   ├── main.py                 # FastAPI app entry point, all core endpoints
│   ├── config.py               # Centralised env-var config
│   ├── schemas.py              # Pydantic request/response models
│   ├── database.py             # SQLAlchemy async engine + session factory
│   ├── models/
│   │   └── user.py             # User SQLAlchemy ORM model
│   ├── routes/
│   │   ├── auth.py             # /auth/register, /auth/login, /auth/me
│   │   ├── projects.py         # /api/projects CRUD + version history
│   │   └── gallery.py          # /api/gallery browse + share
│   ├── services/
│   │   ├── llm_service.py      # Multi-tier LLM + self-correction loop
│   │   ├── rag_service.py      # ChromaDB vector store + retrieval
│   │   ├── cad_runner.py       # Sandboxed build123d script execution
│   │   ├── auth_service.py     # JWT encode/decode, user lookup
│   │   ├── prompts.py          # System prompts + templates (42KB)
│   │   ├── gemini_web_client.py# Reverse-proxy Gemini web client
│   │   └── cleanup.py          # Artifact TTL cleanup manager
│   ├── middleware/
│   │   └── telemetry.py        # Request timing + metrics
│   ├── rag_corpus/
│   │   └── chroma_db/          # Persistent ChromaDB vector store (121 docs)
│   ├── requirements.txt
│   ├── pytest.ini
│   └── test_*.py               # 15+ test files (33 tests total)
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx            # React root mount
│   │   ├── Router.jsx          # Hash-based view router
│   │   ├── App.jsx             # Workbench layout + wiring (~42KB)
│   │   ├── LandingPage.jsx     # Marketing landing page (~80KB)
│   │   ├── api.js              # Typed API client (fetch wrapper)
│   │   ├── index.css           # Global design system styles (~44KB)
│   │   ├── hooks/
│   │   │   ├── useCADWorkbench.js  # Core workbench state (useReducer)
│   │   │   └── useAuth.js          # Auth token state
│   │   ├── components/
│   │   │   ├── Viewer3D.jsx        # React Three Fiber 3D scene
│   │   │   ├── ViewportToolbar.jsx # Camera + visual controls toolbar
│   │   │   ├── ParameterSlider.jsx # Param adjustment UI
│   │   │   ├── ChatModifyPanel.jsx # Chat-to-modify UI
│   │   │   ├── PromptPanel.jsx     # NL prompt input
│   │   │   ├── ProjectSidebar.jsx  # Project/history sidebar
│   │   │   ├── AuthModal.jsx       # Login / register modal
│   │   │   ├── ShareModal.jsx      # Share to gallery modal
│   │   │   ├── OnboardingTour.jsx  # First-run tutorial overlay
│   │   │   ├── GenerationProgress.jsx # SSE streaming progress
│   │   │   ├── CodeInspectorModal.jsx # View generated Python
│   │   │   ├── ErrorBanner.jsx     # Error display
│   │   │   └── TelemetryHUD.jsx    # Debug metrics overlay
│   │   ├── constants/
│   │   └── pages/
│   │       └── Gallery.jsx     # Public gallery page
│   └── package.json
│
├── .github/
│   └── workflows/
│       └── benchmark.yml       # Weekly CI benchmark (GitHub Actions)
├── Dockerfile
├── docker-compose.yml
├── prd.md
├── architecture.md
├── rules.md
├── design.md
├── task.md
└── memory.md
```

---

## 4. Backend Architecture

### 4.1 LLM Pipeline (Multi-Tier Fallback)

```
User Prompt
    |
    v
RAG Retrieve (ChromaDB)
    |  top-3 similar build123d examples
    v
Build System Prompt (few-shot examples injected)
    |
    v
Tier 1: gemini-3.5-flash-lite (google-genai, JSON mode)
    |-- fail -->
Tier 2: gemini-3.6-flash (google-genai)
    |-- fail -->
Tier 3: Groq Llama-3.3-70B (high-speed inference)
    |
    v
Parse JSON Response (robust parser: strict -> non-strict -> regex)
    |
    v
AST Security Validation (block dangerous patterns)
    |
    v
Execute in Subprocess (build123d script, timeout=60s)
    |-- error -->
Self-Correction Loop (up to 3 retries, inject error into prompt)
    |
    v
Export Mesh (trimesh -> STL/STEP/OBJ/GLB)
    |
    v
Return Response (scriptId, parameters, meshUrl, stepUrl, ...)
```

### 4.2 Rate Limiting
- `SimpleRateLimiter`: sliding-window per-IP, memory-efficient (prunes >256 buckets)
- Generate: 10 req/min
- Modify: 10 req/min
- Recompute: 40 req/min

### 4.3 CAD Script Security Model
All generated Python is validated with `ast.parse` before execution. Blocked patterns:
- `subprocess`, `os.system`, `os.popen`
- `exec`, `eval`, `compile`, `__import__`
- `open`, `file`, socket operations

### 4.4 Database Schema
```
users
  id (UUID PK), username, email, hashed_password, created_at

projects
  id (UUID PK), user_id (FK), name, description, created_at, updated_at

project_versions
  id (UUID PK), project_id (FK), script_id, parameters (JSON),
  mesh_info (JSON), python_code, version_number, created_at

gallery_items
  id (UUID PK), project_id (FK), title, description,
  is_public, share_token, created_at
```

### 4.5 RAG Corpus
- **Collection:** `cad_snippets_v1`
- **Documents:** 121 (20 universal archetypes × multiple difficulty levels)
- **Embedding model:** `all-MiniLM-L6-v2` (384-dim, local, no API key)
- **Store:** ChromaDB persistent at `backend/rag_corpus/chroma_db/`
- **Retrieval:** top-3 nearest neighbors at query time

---

## 5. Frontend Architecture

### 5.1 Routing
Hash-based router (`Router.jsx`) — no React Router needed:
```
window.location.hash === ''         -> LandingPage
window.location.hash === '#app'     -> App (Workbench)
window.location.hash === '#gallery' -> Gallery
```

### 5.2 State Management
`useCADWorkbench` hook (`useReducer`) manages all workbench state:
- **Model state:** `scriptId`, `partName`, `parameters`, `paramValues`, `meshUrl`, ...
- **UI state:** `activeTab`, `showCodeModal`, `showShareModal`, `showTour`, ...
- **Viewport state:** `showAxes`, `showGrid`, `materialType`, `visualStyle`, `backgroundTheme`, ...
- **Auth state:** delegated to `useAuth` hook
- **Persistence:** last model serialized to `localStorage` (`cad_last_model`)

### 5.3 3D Rendering Pipeline
```
Backend returns /models/{id}.glb
        |
        v
Viewer3D.jsx (React Three Fiber)
  - useGLTF hook loads GLB
  - OrbitControls (orbit, zoom, pan)
  - Lighting: ambient + directional + point lights
  - Material overrides: CAD Gray / Metallic / Transparent
  - Grid + Axes helpers
  - Dimension annotations
  - TelemetryHUD (FPS, draw calls)
```

### 5.4 API Client (`api.js`)
All requests use native `fetch` with a centralized `API_BASE_URL` constant:
```
Development: http://localhost:8000
Production:  /api (proxied)
```

---

## 6. Deployment

### 6.1 Local Development
```bash
# Backend
cd backend && uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm run dev  # Vite dev server on port 5173
```

### 6.2 Docker
```bash
docker-compose up --build
# Backend: 0.0.0.0:8000
# Frontend: served via nginx or Vite
```

### 6.3 Environment Variables
See `backend/.env.example` for full list. Key variables:
- `GEMINI_API_KEY` — Google Gemini API key
- `GROQ_API_KEY` — Groq API key (fallback LLM)
- `SECRET_KEY` — JWT signing secret
- `ALLOWED_ORIGINS` — CORS origins (comma-separated)
- `ENVIRONMENT` — `development` | `production`

### 6.4 CI/CD
- **GitHub Actions** (`benchmark.yml`): weekly Monday 06:00 UTC
- Runs: schema, AST security, LLM parser, geometry validation, recompute contract tests
- 85% pass rate threshold enforced

---

## 7. Data Flow Diagram

```
Browser
  |-- POST /api/generate (prompt) -->
  |                                   FastAPI main.py
  |                                      |
  |                                   LLMService.generate()
  |                                      |-- RAGService.retrieve() --> ChromaDB
  |                                      |-- Gemini / Groq API call
  |                                      |-- _robust_parse_json()
  |                                      |-- AST validation
  |                                      |
  |                                   CADRunner.execute()
  |                                      |-- subprocess: python build123d_script.py
  |                                      |-- trimesh export (GLB/STL/STEP/OBJ)
  |                                      |
  |<-- JSON response (scriptId, meshUrl, parameters) --
  |
  |-- GET /models/{id}.glb -->
  |<-- Binary GLB stream --
  |
Viewer3D renders mesh
```
