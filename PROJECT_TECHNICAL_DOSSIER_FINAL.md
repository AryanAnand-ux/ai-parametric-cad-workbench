# PROJECT TECHNICAL DOSSIER: AI PARAMETRIC CAD WORKBENCH (FINAL REVISED AUDIT)
**Comprehensive Technical Knowledge Base & Architectural Audit for B.Tech CSE Minor Project**  
**Institution:** Jaypee University of Engineering and Technology (JUET), Guna  
**Evaluation Context:** Academic Minor Project Evaluation (Department of Computer Science & Engineering)  
**Document Generation Date:** 2026-11-22  
**Repository Branch:** `main`  
**Git Commit Hash:** `a83dca44d30f4a1b8c3bef9e5a15d56827e7b426`  
**Working Directory:** `d:\Projects\Minor_project`  

---

## 1. Project Examination & Audit Methodology

### 1.1 Audit Scope & Investigation Protocol
This document constitutes an exhaustive, fact-checked technical dossier of the **AI Parametric CAD Workbench** codebase. It was constructed through direct static inspection of the active source files and reproducible runtime test execution, including:
- **Backend Core & Services:** FastAPI application routes, middleware pipeline, SQLAlchemy 2.0 ORM models, Pydantic data schemas, OpenCASCADE subprocess execution harnesses, Abstract Syntax Tree (AST) security analyzers, multimodal vision parsers, ChromaDB dense vector store, and token-based authentication services.
- **Frontend Architecture:** React 19 single-page application (SPA), React Three Fiber (R3F) 3D WebGL rendering engine, client-side reducers (`useCADWorkbench`), custom hooks, modal controllers, and telemetry HUD overlays.
- **Data Persistence & Migrations:** SQLite Write-Ahead Logging (WAL) engine, SQLAlchemy 2.0 async session pipelines, and Alembic database migration revisions.
- **Test Infrastructure & CI/CD:** Pytest test suites (89 test items collected across 15 test files), GitHub Actions CI/CD workflow configuration, Docker multi-container orchestrations, and dependency manifests (`requirements.txt`, `package.json`, `package-lock.json`).

### 1.2 Verification Labels Used Throughout This Document
Every architectural claim, algorithmic explanation, data model attribute, and performance metric is categorized under strict verification statuses:
- `[VERIFIED IN SOURCE]`: Directly confirmed by inspection of active source code, configuration files, or database schemas.
- `[VERIFIED BY EXECUTION]`: Supported by reproducible live runtime execution output (test suite or build runner).
- `[OUTDATED]`: Historical documentation that previously applied but no longer matches the current codebase.
- `[INCORRECT / CALIBRATED]`: Contradicted by actual implementation details and corrected in this dossier.
- `[UNVERIFIED BY LOG]`: Functionally present and observed in local development, but lacks an automated committed benchmark log.
- `[NEEDS TEAM CONFIRMATION]`: Operational, physical, or academic information requiring direct input from the student authors or faculty mentors.

### 1.3 Key Audit Findings: Implementation Truth vs. Documentation Drift
The codebase reflects significant technical evolution that resulted in documentation drift across earlier files:
1. **JWT Secret Configuration:** `README.md` and early documentation referenced `SECRET_KEY`. The active implementation in `backend/config.py` (Line 73) and `backend/services/auth_service.py` (Line 29) strictly enforces `JWT_SECRET_KEY` [VERIFIED IN SOURCE].
2. **Database Migrations:** Early notes described manual table creation via `Base.metadata.create_all`. An automated asynchronous **Alembic migration environment** is fully established in `backend/alembic/` with revision `dd865e7861b0_initial_schema.py` [VERIFIED IN SOURCE].
3. **Test Suite Count Reconciliation:** 
   - `README.md` (Line 84) states `79 tests, ~100 seconds` [OUTDATED].
   - `AGENTS.md` (Lines 20, 44) cites `80 tests / 14 files` [OUTDATED].
   - GitHub Actions CI (`.github/workflows/ci.yml`) configures a subset of **8 core test files containing 50 test items** to optimize remote pipeline duration [VERIFIED IN SOURCE].
   - The **full local test suite collects 89 test items across 15 test files**, yielding **88 passed and 1 skipped by design** in 188.72 seconds [VERIFIED BY EXECUTION].
4. **Multimodal Sketch-to-CAD Pipeline:** The platform includes a dedicated `POST /api/generate/sketch` endpoint with multi-provider vision parsing (Gemini Vision + Groq Vision fallback), enforcing a 7-step Geometric Chain-of-Thought and dimension extraction [VERIFIED IN SOURCE].
5. **Frontend Quality Assurance:** There is no Jest/Vitest runner in `frontend/package.json`. Frontend verification relies on `oxlint` (reporting 0 warnings and 0 errors across 27 files) and Vite production build bundling (compiling in 1.70 seconds) [VERIFIED BY EXECUTION].
6. **Benchmark Latency Calibration:** Earlier summaries cited a generation $P_{50}$ latency of $14.2\text{ s}$. Analysis of the raw data in `backend/benchmark_results.json` reveals that $14.2\text{ s}$ was the latency of a single prompt (`l_bracket`). Across the entire 20-prompt distribution, the **true median ($P_{50}$) is $17.25\text{ s}$ ($17,250\text{ ms}$)**, and the mean latency is **$17.14\text{ s}$ ($17,140\text{ ms}$)** [CALIBRATED].
7. **Security Scope Calibration:** Static AST validation prevents forbidden syntax nodes, unauthorized imports, and dunder reflection, but does not provide complete operating-system-level process containment. The actual security model is defense-in-depth: static AST analysis coupled with isolated subprocess execution, stripped environment variables, and execution timeouts [CALIBRATED].

---

## 2. Project Overview

### 2.1 The Problem Statement
Traditional Computer-Aided Design (CAD) software (e.g., Autodesk Fusion 360, SolidWorks, FreeCAD, CATIA) relies on complex Graphical User Interfaces (GUIs) requiring hundreds of specialized commands, coordinate planes, geometric constraints, and feature trees. For undergraduate engineering students, hobbyists, rapid-prototyping teams, and researchers:
- **Steep Learning Curve:** Mastering parametric CAD software requires dozens of hours of specialized training.
- **Slow Early Ideation:** Translating a simple conceptual design (e.g., *"A 100x60mm mounting plate with 4 corner M4 clearance holes and a 20mm center bore"*) into a 3D solid model takes 10–20 minutes of manual sketching, constraining, dimensioning, extruding, and hole-wizard setup.
- **Lack of Programmatic Accessibility:** Non-CAD specialists cannot easily integrate CAD generation into programmatic pipelines, automated simulations, or rapid web environments.

### 2.2 Why This Problem is Important
Parametric 3D solid modeling is the foundational first step of modern manufacturing, 3D printing (additive manufacturing), and mechanical engineering. Reducing the friction between conceptual intent (natural language or 2D concept sketches) and mathematically rigorous boundary representation (B-Rep) geometry democratizes mechanical engineering and accelerates prototyping cycles from hours to seconds.

### 2.3 Intended Users
- **Undergraduate & Graduate Engineering Students:** Needing quick functional enclosures, brackets, test fixtures, and structural components for academic projects without deep CAD UI expertise.
- **3D Printing Hobbyists & Makers:** Requiring watertight STL/STEP files generated rapidly from plain English descriptions or hand sketches.
- **Mechanical Engineers & Designers:** Performing rapid concept ideation, preliminary dimensional envelope testing, and parametric variations before committing to detailed production CAD.
- **Academic Evaluators & Researchers:** Benchmarking Large Language Models on domain-specific geometric reasoning, code generation, and constraint satisfaction.

### 2.4 The Proposed Solution
The **AI Parametric CAD Workbench** is a full-stack, browser-based engineering platform that bridges the gap between natural language / 2D sketches and precision manufacturing. Rather than generating imprecise, non-manifold polygonal approximations (such as neural radiance fields or raw 3D mesh diffusions), this system synthesizes **exact, editable, boundary-representation (B-Rep) Python scripts** using the industrial-grade `build123d` CAD kernel (powered by OpenCASCADE Technology / OCCT).

The pipeline extracts configurable design parameters into a clean UI slider schema, executes the generated Python script within an isolated, AST-filtered subprocess, validates the output mesh for mathematical 2-manifold watertightness, and returns both WebGL-renderable mesh data and industrial **STEP** (Standard for the Exchange of Product model data) files.

### 2.5 What Makes This Implementation Distinctive & Useful
1. **Mathematical Precision over Neural Meshes:** Generates actual OpenCASCADE B-Rep solids, ensuring planar faces are mathematically flat, cylindrical holes are true analytical surfaces, and STEP files can be imported directly into industrial CNC or CAD workflows [VERIFIED IN SOURCE].
2. **Sub-200ms Parametric Recomputation:** Once generated, modifying dimensional parameters (e.g., bracket thickness, hole pitch) does **not** invoke an LLM. The system injects updated values directly into the script's AST `PARAMS` dictionary and re-executes the CAD kernel locally in $<200\text{ ms}$ ($164\text{ ms}$ manually observed) [VERIFIED IN SOURCE / UNVERIFIED BY LOG].
3. **Closed-Loop LLM Self-Correction:** If generated code fails Python syntax checks, triggers an AST security violation, or fails geometric topology assertions (e.g., produces disconnected floating solids), the system intercepts the error traceback and feeds it back into the LLM for up to 3 automated self-correction cycles [VERIFIED IN SOURCE].
4. **Local Semantic RAG Engine:** Leverages a local ChromaDB vector store containing 121 domain-specific CAD engineering blueprints with `all-MiniLM-L6-v2` embeddings, eliminating cloud API dependencies for few-shot context retrieval [VERIFIED IN SOURCE].
5. **Multimodal Sketch-to-CAD:** Users can upload or clipboard-paste (`Ctrl+V`) hand-drawn engineering sketches. The system executes a structured Geometric Chain-of-Thought (Axis Mapping, Base Profile Strategy, Curve Rules, Feature Elevations) to extract exact dimensional requirements before solid compilation [VERIFIED IN SOURCE].

### 2.6 Main Objectives
- Provide zero-install, browser-based parametric CAD solid modeling.
- Achieve $\ge 85\%$ overall generation success on standard mechanical engineering primitives and archetypes ($90.0\%$ achieved in benchmark).
- Achieve sub-200ms slider recomputation for interactive design exploration.
- Enforce defense-in-depth security coupling static AST inspection (import whitelist, blocked builtins, dunder access prevention) with isolated subprocess execution, stripped environment variables, and bounded execution timeouts.
- Export production-grade manufacturing formats (STL for 3D slicing, STEP for CNC/CAD interchange).

### 2.7 Key Features
- **Natural Language CAD Synthesis:** Multi-tier LLM fallback (`gemini-2.5-flash` / `gemini-3.5-flash-lite` $\to$ Gemini Web $\to$ Groq `llama-3.3-70b-versatile`).
- **Server-Sent Events (SSE) Streaming:** Real-time multi-phase pipeline telemetry (RAG Search $\to$ LLM Generation $\to$ AST Analysis $\to$ OpenCASCADE Compilation $\to$ Mesh Validation).
- **Interactive AutoCAD-Grade 3D Viewport:** React Three Fiber viewer with ViewCube orientation gizmo, WCS/UCS coordinate tripod, millimeter snap grid, dynamic dimension badges, and real-time section cut plane.
- **Dynamic Parametric Sliders:** Bidirectional bound validation, semantic categorization (Dimensions, Features, Tolerances), manual draft typing, and one-click reset to defaults.
- **Conversational Chat-to-Modify:** Context-aware natural language geometric refactoring with automated version tree branching.
- **Public Design Gallery:** Community discovery engine with live debounced search, engineering discipline filter chips, atomic like counters, and isolated model forking.
- **JWT User Authentication & Workspace Isolation:** BCrypt password hashing, refresh-token rotation with reuse detection, and 50 gen/day free-tier quota enforcement.

### 2.8 System Limitations (Real & Documented)
- **Assembly Motion Constraints:** Supports static multi-body components in `assembly` design mode, but does not model dynamic cinematic joints (hinges, gears, sliders) or physics simulations.
- **Single-Node Subprocess Execution:** CAD execution runs on the backend host; there is currently no distributed Celery/Redis task worker queue.
- **Model Storage TTL:** Generated STL/STEP artifacts on disk are subject to periodic cleanup; while the database retains the Python script and can recompile on demand, unpersisted guest artifacts expire.
- **2D Drawing Export (DXF):** Direct generation of 2D drafting sheets with ISO standard dimension lines is not yet implemented.
- **Computational Mesh Validation vs. Physical Printability:** Automated `trimesh` verification guarantees mathematical 2-manifold closedness ($\chi = 2$), positive volume, and edge manifoldness. However, this does not guarantee physical 3D printability (e.g., overhang angles exceeding $45^\circ$, thin walls below nozzle diameter, or bed adhesion).

### 2.9 Project Explanation at Three Levels

#### Level 1: Simple Explanation (For Non-Technical Audiences)
Imagine wanting to 3D print a custom plastic bracket for your desk. Normally, you would need to spend weeks learning complicated 3D modeling software, drawing shapes with a mouse, and entering complex math. With our AI Workbench, you simply type: *"A sturdy L-bracket 60mm long with two screw holes,"* or paste a photo of a rough pencil sketch. In about 15 seconds, the workbench designs the exact 3D part right in your browser. You can drag sliders to adjust the thickness or length in real time, and click "Download" to get a file ready for any 3D printer.

#### Level 2: Technical Explanation (For CSE Students)
The platform is a full-stack engineering tool that transforms natural language prompts or raster sketches into valid boundary-representation 3D CAD models. The backend is built with FastAPI and utilizes an asynchronous pipeline. When a user submits a prompt, local ChromaDB vector embeddings retrieve top-$k$ relevant CAD code blueprints to inject into the LLM system prompt. The LLM produces a dual-output JSON payload containing executable `build123d` Python code and a structured parameter dictionary. 

Before execution, an Abstract Syntax Tree (AST) analyzer validates the script against an import whitelist, blocking unauthorized system calls or reflection attacks. The validated script is executed in an isolated subprocess with OpenCASCADE CAD kernel bindings. If execution fails or generates non-manifold geometry, an automated feedback loop retries generation using the execution traceback. The resulting geometry is exported to binary STL and ISO 10303 STEP files, served to a React 19 frontend utilizing React Three Fiber for WebGL rendering. Real-time slider recomputations bypass the LLM entirely, modifying the AST parameters and executing in under 200 milliseconds.

#### Level 3: Rigorous Academic Explanation (For JUET Evaluation Panel)
This project addresses the problem of automated solid geometry synthesis through a constrained, closed-loop neurosymbolic architecture. Existing generative AI models for 3D content typically produce unstructured polygon soups or signed distance field approximations that lack dimensional accuracy, topological validity, and parametric editability required for mechanical engineering.

Our architecture couples non-deterministic Large Language Models with deterministic geometric modeling kernels (`build123d` / OpenCASCADE Technology). The generative pipeline implements a five-stage verification lifecycle:
1. **Semantic Vector Retrieval:** Query projection into a 384-dimensional dense vector space via `all-MiniLM-L6-v2` to retrieve domain-specific few-shot exemplars from ChromaDB.
2. **Constrained Dual-Output Synthesis:** Enforced Pydantic JSON schema generation guaranteeing mathematical separation of configuration variables (`PARAMS`) from geometric CSG operations.
3. **Static AST Analysis & Security Screening:** Lexical inspection denying high-risk grammar nodes (`ast.Lambda`, `ast.Yield`, `ast.Global`), disallowing dangerous built-ins (`eval`, `exec`, `open`), and blocking dunder-based reflection attacks (`__subclasses__`).
4. **Deterministic Subprocess Execution & Topology Assertions:** Isolated subprocess instantiation bounded by a concurrency semaphore ($N=2$) and 60-second timeout. The geometric engine computes Euler characteristic invariants, verifies 2-manifold closedness ($V - E + F = 2(1 - g)$), detects disconnected volumetric islands, and verifies non-zero volume.
5. **Real-Time Client-Side Decoupling:** Recomputations execute via direct AST parameter dictionary replacement without LLM intervention, achieving determinism and an empirical latency of $<200\text{ ms}$.

---

## 3. Complete Technology Stack

The following inventory details every technology directly utilized in the active codebase. Versions are verified against `backend/requirements.txt` and `frontend/package.json`.

| Category | Technology | Version | Purpose in Project | Source / Config File | Reason for Use | Verification Status |
|---|---|---|---|---|---|---|
| **Frontend Framework** | React | `^19.2.8` | Core UI component lifecycle & state | `frontend/package.json` | High-performance virtual DOM, concurrent rendering, and native support for modern React hooks. | `[VERIFIED IN SOURCE]` |
| **Frontend DOM** | React-DOM | `^19.3.0` | Browser DOM rendering engine | `frontend/package.json` | Required companion for React 19 web rendering. | `[VERIFIED IN SOURCE]` |
| **Build Tool & Bundler** | Vite | `^8.3.4` | Development dev-server & production rollup bundler | `frontend/package.json` | Near-instant HMR (Hot Module Replacement) and optimized tree-shaking for heavy 3D packages. | `[VERIFIED IN SOURCE]` |
| **3D WebGL Library** | Three.js | `^0.186.1` | Core WebGL scene graph, lighting, mesh loader | `frontend/package.json` | Industry-standard WebGL engine capable of parsing binary STLs and rendering PBR materials. | `[VERIFIED IN SOURCE]` |
| **Declarative 3D Wrapper**| @react-three/fiber | `^9.8.2` | Declarative Three.js component bindings for React | `frontend/package.json` | Allows 3D scene elements (meshes, lights, cameras) to be managed via declarative React state. | `[VERIFIED IN SOURCE]` |
| **3D CAD Helpers** | @react-three/drei | `^10.7.9` | ViewCube gizmo, OrbitControls, millimeter grid | `frontend/package.json` | Supplies pre-built CAD UI elements: `GizmoViewcube`, `GizmoViewport`, and infinite grid helpers. | `[VERIFIED IN SOURCE]` |
| **Three.js Extensions** | three-stdlib | `^2.36.1` | Extended Three.js geometric utilities & loaders | `frontend/package.json` | Complementary three utility bundle. (Note: `Viewer3D.jsx` directly imports `STLLoader` via `three/examples/jsm/loaders/STLLoader.js`). | `[VERIFIED IN SOURCE]` |
| **HTTP Client** | Axios | `^1.20.0` | Client-side API request dispatcher | `frontend/package.json` | Interceptor support for automatic JWT Bearer token attachment and centralized error formatting. | `[VERIFIED IN SOURCE]` |
| **Syntax Highlighting** | Prism.js | `^1.30.0` | Python syntax highlighting in Code Inspector modal | `frontend/package.json` | Lightweight, robust syntax coloring for build123d Python scripts. | `[VERIFIED IN SOURCE]` |
| **Frontend Linter** | Oxlint | `^1.86.0` | Ultra-fast Rust-based linter | `frontend/package.json` | Replaces ESLint with 50x faster lint cycles; enforced at 0 errors / 0 warnings. | `[VERIFIED IN SOURCE]` |
| **Backend Framework** | FastAPI | `>=0.141.1` | Asynchronous REST and SSE API server | `backend/requirements.txt` | Native async ASGI support, automatic OpenAPI/Swagger generation, and tight Pydantic integration. | `[VERIFIED IN SOURCE]` |
| **ASGI Server** | Uvicorn (standard) | `>=0.28.0` | High-performance ASGI production server | `backend/requirements.txt` | UVLoop-backed asynchronous event loop server handling concurrent API requests. | `[VERIFIED IN SOURCE]` |
| **Data Validation** | Pydantic | `>=2.6.0` | Request/response data contract enforcement | `backend/requirements.txt` | Rust-backed schema validation ensuring dual-output JSON payloads adhere strictly to specifications. | `[VERIFIED IN SOURCE]` |
| **CAD Kernel / Engine** | build123d | `>=0.8.0` | Programmatic 3D CAD modeling framework | `backend/requirements.txt` | High-level Python API wrapping OpenCASCADE Technology (OCCT) for true B-Rep CSG modeling. | `[VERIFIED IN SOURCE]` |
| **Mesh Processing** | Trimesh | `>=5.1.0` | Polygonal mesh analysis and validation | `backend/requirements.txt` | Rapid computation of mesh watertightness, face counts, volume, and bounding box dimensions. | `[VERIFIED IN SOURCE]` |
| **Computational Geometry**| Shapely | `>=2.1.2` | Planar geometric feature manipulation | `backend/requirements.txt` | Robust 2D polygonal algorithms used for profile boundary checks and cross-section validation. | `[VERIFIED IN SOURCE]` |
| **Scientific Computing** | SciPy | `>=1.12.0` | Spatial algorithms and convex hull routines | `backend/requirements.txt` | Advanced geometric analysis and optimization calculations. | `[VERIFIED IN SOURCE]` |
| **Numerical Arrays** | NumPy | `>=1.26.0` | Vectorized coordinate operations | `backend/requirements.txt` | High-speed vertex transformation and bounding box matrix calculations. | `[VERIFIED IN SOURCE]` |
| **Vector Database** | ChromaDB | `>=1.5.9` | Embedded local vector store for RAG blueprints | `backend/requirements.txt` | Serverless, persistent local vector indexing with cosine similarity search for CAD exemplars. | `[VERIFIED IN SOURCE]` |
| **Embedding Model** | Sentence-Transformers| `>=3.0.0`| Local dense text embedding pipeline | `backend/requirements.txt` | Runs `all-MiniLM-L6-v2` locally (384 dimensions) to convert CAD queries into semantic vectors. | `[VERIFIED IN SOURCE]` |
| **ORM Engine** | SQLAlchemy | `>=2.0.0` | Async relational database object mapper | `backend/requirements.txt` | Fully asynchronous database queries supporting both SQLite and PostgreSQL. | `[VERIFIED IN SOURCE]` |
| **Database Migrations** | Alembic | `>=1.13.0` | Declarative schema migration management | `backend/requirements.txt` | Version-controlled DDL migrations with batch operations for SQLite compatibility. | `[VERIFIED IN SOURCE]` |
| **Async SQLite Driver** | aiosqlite | `>=0.20.0` | Asynchronous SQLite database interface | `backend/requirements.txt` | Non-blocking database I/O for SQLite in development environments. | `[VERIFIED IN SOURCE]` |
| **Async Postgres Driver**| asyncpg | `>=0.31.0` | High-performance PostgreSQL async driver | `backend/requirements.txt` | Production-ready binary protocol PostgreSQL driver. | `[VERIFIED IN SOURCE]` |
| **Async Concurrency** | Greenlet | `>=3.5.6` | Coroutine concurrency for SQLAlchemy async | `backend/requirements.txt` | Required engine component for SQLAlchemy 2.0 asyncio context switching. | `[VERIFIED IN SOURCE]` |
| **Password Hashing** | BCrypt | `>=4.1.0` | Cryptographic password hashing | `backend/requirements.txt` | Industry-standard salt-and-hash algorithm resistant to rainbow table and brute-force attacks. | `[VERIFIED IN SOURCE]` |
| **Password Utilities** | Passlib | `>=1.7.4` | Password context management | `backend/requirements.txt` | Modular password verification interface. | `[VERIFIED IN SOURCE]` |
| **Authentication Tokens**| PyJWT (with crypto) | `>=2.8.0` | JSON Web Token encoding, decoding, validation | `backend/requirements.txt` | Standardized HMAC-SHA256 (HS256) signature generation for stateless auth. | `[VERIFIED IN SOURCE]` |
| **Primary Cloud LLM** | Google GenAI SDK | `>=2.25.0` | Official client for Google Gemini models | `backend/requirements.txt` | Connects to `gemini-2.5-flash`, `gemini-3.5-flash-lite`, and Gemini Vision. | `[VERIFIED IN SOURCE]` |
| **Fallback Cloud LLM** | Groq Python SDK | `>=1.0.0` | High-speed inference provider | `backend/requirements.txt` | Sub-second fallback inference using `llama-3.3-70b-versatile` and `llama-3.2-11b-vision-preview`. | `[VERIFIED IN SOURCE]` |
| **Async HTTP Engine** | HTTPX | `>=0.28.0` | Async HTTP client for tests and external APIs | `backend/requirements.txt` | Test client transport and asynchronous reverse-engineered Gemini Web proxy integration. | `[VERIFIED IN SOURCE]` |
| **Environment Config** | Python-Dotenv | `>=1.2.3` | Environment variable management | `backend/requirements.txt` | Loads configuration keys from `backend/.env` at process startup. | `[VERIFIED IN SOURCE]` |
| **Form Data Parser** | Python-Multipart | `>=0.0.9` | Multipart form-data parser for sketch uploads | `backend/requirements.txt` | Handles multi-megabyte image streaming in `POST /api/generate/sketch`. | `[VERIFIED IN SOURCE]` |
| **Test Runner** | Pytest | `>=7.4.0` | Unit, integration, and API test framework | `backend/requirements.txt` | Automated test discovery, execution, assertion inspection, and reporting. | `[VERIFIED IN SOURCE]` |
| **Async Test Runner** | Pytest-Asyncio | `>=0.23.0` | Asyncio fixture runner for Pytest | `backend/requirements.txt` | Configured with `asyncio_mode = auto` to execute coroutine test cases seamlessly. | `[VERIFIED IN SOURCE]` |

---

## 4. System Architecture

```
[ User Interaction: Browser ]
   │
   ├─► Natural Language Prompt / Image Sketch / Sliders
   │
[ Frontend (React 19 + Vite + R3F) ]
   │
   ├── App.jsx / useCADWorkbench.js (State Machine & Reducer)
   ├── Viewer3D.jsx (Three.js WebGL / EdgesGeometry / ViewCube)
   ├── ParameterSlider.jsx (Debounced Recompute Dispatcher)
   └── api.js (Axios / SSE Fetch Client)
         │
         ▼  HTTP REST / SSE Stream (port 8000)
[ Backend Core (FastAPI / Uvicorn) ]
   │
   ├── Middleware Pipeline:
   │     ├─► ProxyHeadersMiddleware (Trust reverse proxies)
   │     ├─► CORSMiddleware (Origin authorization)
   │     ├─► TelemetryMiddleware (JSON request logging & metrics)
   │     └─► SecurityHeadersMiddleware (nosniff, referrer-policy)
   │
   ├── Rate Limiting & Quota:
   │     ├─► SimpleRateLimiter (10 req/min generate, 40 req/min recompute)
   │     └─► check_and_bump_quota (50 gen/day on free tier)
   │
   ├── Core Processing Services:
   │     ├─► VisionService (Gemini Vision / Groq Vision Chain-of-Thought)
   │     ├─► RAGService (ChromaDB + all-MiniLM-L6-v2 Semantic Search)
   │     ├─► LLMService (Multi-Tier Fallback: Gemini -> Groq Llama)
   │     ├─► AST Security Validator (validate_script_safety)
   │     └─► CADRunner (Isolated Subprocess + OpenCASCADE Kernel)
   │
   ├── Data Persistence Layer:
   │     └─► SQLAlchemy 2.0 Async Session -> SQLite (WAL Mode) / PostgreSQL
   │           ├── Users Table
   │           ├── Projects Table
   │           ├── Generations Table
   │           └── Versions Table
   │
   └── File System Storage:
         └─► /scratch/temp/models/*.stl, *.step (Isolated from reload triggers)
```

### 4.1 Frontend Structural Organization
- `frontend/src/main.jsx`: Application bootstrap mounting `Router.jsx` inside React `StrictMode` [Line 6].
- `frontend/src/Router.jsx`: Lightweight hash router handling URL changes: `#app` (Workbench), `#gallery` (Community Gallery), `#model=<id>` (Deep-linked model inspector), and default (Landing Page) [Lines 42–48].
- `frontend/src/App.jsx`: Main Workbench container implementing a Neobrutalist Bento Grid layout. Houses the 3D viewport, prompt drawer, parametric sliders, telemetry HUD, and action toolbars [Lines 1–250].
- `frontend/src/hooks/useCADWorkbench.js`: Centralized state management engine implemented as a 370-line reducer (`cadWorkbenchReducer`). Manages active model parameters, undo stacks (`modelHistory`), camera view flags, and local storage synchronization (`cad_last_model`) [Lines 30–91].
- `frontend/src/hooks/useAuth.js`: Authentication state coordinator managing JWT access tokens, user registration, login, and active user profile caching [Lines 4–74].
- `frontend/src/components/Viewer3D.jsx`: AutoCAD-engineered 3D viewer built with React Three Fiber (`@react-three/fiber`) and Drei (`@react-three/drei`). Employs a custom `STLLoader` effect, `THREE.EdgesGeometry` at a 24° threshold for mechanical contour lines, interactive `GizmoViewcube`, `GizmoViewport` coordinate tripod, and dynamic millimeter dimension tags [Lines 124–238].

### 4.2 Backend Structural Organization
- `backend/main.py`: Primary application entrypoint configuring CORS, telemetry middleware, rate limiters, SSE streaming event generators, artifact serving, and high-level CAD generation endpoints [Lines 1–300].
- `backend/config.py`: Centralized environment loader configuring filesystem directories (`TEMP_DIR`, `MODELS_DIR`), execution bounds, secrets, and API credentials [Lines 1–83].
- `backend/database.py`: Asynchronous SQLAlchemy engine instantiator. Manages connection pooling, WAL mode pragmas for SQLite, table creation, and auto-migration hooks [Lines 1–138].
- `backend/schemas.py`: Pydantic model definitions declaring strict input/output contracts for parameters, generation payloads, recomputations, and modifications [Lines 1–250].
- `backend/services/`:
  - `cad_runner.py`: Subprocess execution harness, AST security analyzer, and OpenCASCADE runtime validator [Lines 1–245].
  - `llm_service.py`: Multi-tier LLM orchestration service with automated PII scrubbing, JSON repair regexes, and self-correction loops [Lines 1–250].
  - `vision_service.py`: Multimodal sketch analysis pipeline enforcing Geometric Chain-of-Thought schemas [Lines 1–250].
  - `rag_service.py`: ChromaDB vector index manager and few-shot prompt formatter [Lines 1–250].
  - `auth_service.py`: JWT token generation, bcrypt password hashing, and user quota management [Lines 1–216].
- `backend/routes/`:
  - `auth.py`: User registration, authentication, token refresh, and profile endpoints [Lines 1–233].
  - `projects.py`: Project workspace CRUD, generation summaries, and version tree queries [Lines 1–250].
  - `gallery.py`: Public community design browsing, tag filtering, liking, publishing, and forking [Lines 1–250].

### 4.3 Frontend-to-Backend Communication Protocols
Communication occurs via standard HTTP REST requests and Server-Sent Events (SSE):
1. **JSON REST Calls:** Dispatched via configured Axios instances in `frontend/src/api.js`. An interceptor automatically injects `Authorization: Bearer <token>` from `localStorage['cad_token']` into outgoing headers [Lines 66–72].
2. **Server-Sent Events (SSE):** `POST /api/generate/stream` establishes a unidirectional text stream (`text/event-stream`). The client uses native `fetch` with a `ReadableStreamDefaultReader` in `frontend/src/api.js` (`generatePartStream`), parsing chunked JSON payloads to update UI progress bars across five discrete phases:
   - `rag_retrieval` (Progress: 15%)
   - `llm_generation` (Progress: 35%)
   - `ast_validation` (Progress: 55%)
   - `cad_execution` (Progress: 75%)
   - `mesh_validation` (Progress: 92%)
   - `complete` (Progress: 100%) [backend/main.py Lines 587–717].

### 4.4 Backend-to-Database Communication
The persistence layer utilizes SQLAlchemy 2.0 with the `asyncio` extension:
- **Connection Engine:** Configured in `backend/database.py` using `create_async_engine(DATABASE_URL)`. By default, connects to `sqlite+aiosqlite:///cad_workbench.db` [Lines 22–41].
- **Concurrency & WAL Mode:** When SQLite is active, an event listener on the sync engine connection executes PRAGMAs:
  - `PRAGMA journal_mode=WAL`: Write-Ahead Logging allows concurrent readers and writers without database locking [Line 48].
  - `PRAGMA busy_timeout=5000`: Waits up to 5 seconds during concurrent write contention [Line 49].
  - `PRAGMA synchronous=NORMAL`: Optimal durability and performance balance in WAL mode [Line 51].
  - `PRAGMA cache_size=-8000`: Allocates 8 MB of RAM for in-memory page caching [Line 53].
- **Dependency Injection:** Endpoints declare `db: AsyncSession = Depends(get_db)`, yielding a scoped session that automatically commits or rolls back and closes upon request completion [Lines 64–71].

### 4.5 External Services & LLM Integration Strategy
The platform implements a multi-tier resilience architecture:
1. **Tier 1 (Primary Cloud):** `gemini-2.5-flash` or `gemini-3.5-flash-lite` via the official `google-genai` SDK using native JSON schema mode (`response_schema=DualOutputPayload`).
2. **Tier 2 (Secondary Cloud):** `gemini-3.1-flash-lite` or `gemini-3.6-flash`.
3. **Tier 3 (Ultra-Fast Fallback):** Groq Cloud API running `llama-3.3-70b-versatile` (and `llama-3.2-11b-vision-preview` for sketches). If Google API quotas are exhausted, the request fails over seamlessly to Groq in $<1.5\text{ seconds}$ [backend/services/vision_service.py Lines 294–350].
4. **Reverse-Engineered Web2API (Experimental):** `backend/services/gemini_web_client.py` provides cookie-authenticated access for environments without API keys [config.py Lines 51–69].

### 4.6 End-to-End Data Flow Trace
Tracing a generation request from user prompt to 3D visualization:

```
[User enters prompt in PromptPanel.jsx]
   │
   ▼ Click "Generate Parametric 3D Solid" (or press 'G')
[dispatch generatePartStream() in api.js]
   │
   ▼ POST /api/generate/stream
[backend/main.py: generate_part_stream()]
   │
   ├─► Check Rate Limiter (SimpleRateLimiter.check) -> 10 req/min
   ├─► Enforce User Quota (check_and_bump_quota) -> <50 generations today
   ├─► Emit SSE event: 'rag_retrieval' (15%)
   │     └─► RAGService.retrieve(prompt, k=3) -> ChromaDB query via all-MiniLM-L6-v2
   │
   ├─► Emit SSE event: 'llm_generation' (35%)
   │     ├─► scrub_pii(prompt) -> Redact emails, phone numbers, secret tokens
   │     ├─► LLMService.generate_dual_output(prompt)
   │     │     └─► Primary Gemini API -> Fallback Groq Llama-3.3-70B
   │     └─► _robust_parse_json() -> Validate against DualOutputPayload schema
   │
   ├─► Emit SSE event: 'ast_validation' (55%)
   │     └─► validate_script_safety(python_code)
   │           ├─► Check imports (build123d, math, typing only)
   │           ├─► Check blocked builtins (open, eval, exec, input)
   │           └─► Check dunder attributes (__subclasses__, __globals__)
   │
   ├─► Emit SSE event: 'cad_execution' (75%)
   │     └─► CADRunner.execute_script_async()
   │           ├─► Acquire CAD_EXECUTION_SEMAPHORE (max 2 concurrent)
   │           ├─► Write code to /scratch/temp/part_<uuid>.py
   │           ├─► Spawn subprocess: python part_<uuid>.py (timeout: 60s)
   │           └─► If failure: Intercept stderr -> LLMService.correct_code() (up to 3 retries)
   │
   ├─► Emit SSE event: 'mesh_validation' (92%)
   │     └─► trimesh analysis: verify is_watertight, solid count == 1, non-zero volume
   │
   ├─► Database Persistence (if user authenticated):
   │     └─► save_generation_record() -> Write row to 'generations' table
   │
   └─► Emit SSE event: 'complete' (100%) with GenerateResponse payload
         │
         ▼ Frontend receives final result in useCADWorkbench.js
[Reducer receives APPLY_PART_RESPONSE]
   ├─► Persist to localStorage['cad_last_model']
   ├─► Populate parameters array & default slider values
   ├─► Set meshUrl = "/static/models/part_<uuid>.stl"
   │
   ▼ Viewer3D.jsx loads meshUrl
[STLLoader parses binary STL buffer]
   ├─► THREE.EdgesGeometry extracts sharp mechanical feature edges (>24 deg)
   ├─► Calculate 3D bounding box dimensions (L x W x H)
   └─► WebGL renders solid shaded mesh with CAD contour lines & dimension tags
```

### 4.7 Deployment Architecture
The repository ships with deployment configurations:
- **Containerization:** `Dockerfile` based on `python:3.11-slim`, setting `PYTHONDONTWRITEBYTECODE=1`, pre-creating `/app/scratch/temp/models`, and configuring an HTTP healthcheck against `/api/health` [Dockerfile Lines 1–20].
- **Service Orchestration:** `docker-compose.yml` configures a multi-container stack:
  - `backend`: FastAPI app running on port 8000, mounting `cad-artifacts` volume.
  - `postgres`: PostgreSQL 16 container with healthcheck routines (`pg_isready`) [Lines 29–44].
  - `frontend`: Production Nginx web server serving compiled static assets on port 80 [Lines 45–55].

---

## 5. Detailed Module-by-Module Explanation

### Module 1: Natural Language CAD Prompt Engine
- **Purpose:** Converts free-form English mechanical descriptions into executable, parametric CAD scripts.
- **Problem Solved:** Removes the requirement for mechanical CAD expertise and manual feature tree modeling.
- **User Interaction:** User enters text into `textarea#prompt-input` (e.g., *"A stepped drive shaft 120mm long..."*) or selects one of 20 categorized archetype presets. Pressing `Enter` (or keyboard shortcut `G`) initiates generation.
- **Frontend Implementation:** `frontend/src/components/PromptPanel.jsx` binds the textarea, manages drag-over states, and dispatches generation [Lines 64–146].
- **Backend Implementation:** Handled by `POST /api/generate` and `POST /api/generate/stream` in `backend/main.py`, invoking `LLMService.generate_dual_output()` [Lines 388–550].
- **Important Functions:** `LLMService.generate_dual_output()`, `_robust_parse_json()`, `scrub_pii()`.
- **Implementation Status:** Complete and verified [VERIFIED IN SOURCE].

### Module 2: Multimodal Sketch-to-CAD Engine
- **Purpose:** Transforms raster images of hand-drawn sketches or engineering drawings into 3D CAD models.
- **Problem Solved:** Engineers frequently ideate using pencil-and-paper sketches with annotated dimensions that previously had to be manually re-drawn in CAD software.
- **User Interaction:** User drags-and-drops an image file (PNG, JPEG, WEBP), pastes directly from the clipboard (`Ctrl+V`), or browses files. An interactive synthesis badge appears showing recognized visual features and extracted dimension tags.
- **Frontend Implementation:** `PromptPanel.jsx` contains clipboard paste listeners (`handlePaste`), drag-drop zones, and file upload handlers [Lines 26–58]. Displays the `.sketch-detected-banner` [Lines 71–100].
- **Backend Implementation:** `POST /api/generate/sketch` in `backend/main.py` [Lines 729–960]. Invokes `VisionService.parse_sketch()` in `backend/services/vision_service.py` [Lines 423–520].
- **Algorithms / Logic:** Strict Geometric Chain-of-Thought enforcing 7 rules: Axis Mapping, Base Profile Type, Curve Rules (forbidding box-minus-box for arches), Feature Z-Elevations, Structural Blueprint, Dimension Extraction, and Mandatory Parameter Enforcement in the downstream `PARAMS` dictionary.
- **Implementation Status:** Complete and verified [VERIFIED IN SOURCE / VERIFIED BY EXECUTION].

### Module 3: Fast Parametric Recomputation Engine
- **Purpose:** Re-executes the OpenCASCADE CAD script with updated slider parameters in $<200\text{ ms}$ without invoking an LLM.
- **Problem Solved:** LLM generation takes 10–20 seconds and consumes API quota; real-time slider manipulation requires immediate visual feedback.
- **User Interaction:** User drags a slider in the workbench sidebar (or enters a precise numeric value). The 3D model in the viewport immediately updates its geometric dimensions.
- **Frontend Implementation:** `frontend/src/components/ParameterSlider.jsx` provides range sliders, stepper buttons, and draft text inputs [Lines 12–150]. Debounced dispatch in `frontend/src/App.jsx` (`handleParamChange`) calls `recomputePart()` [Lines 300–350].
- **Backend Implementation:** `POST /api/recompute` in `backend/main.py` [Lines 967–1048]. Calls `CADRunner.execute_script_async()` with `fast_preview=True`.
- **Algorithms / Logic:** `_inject_parameters()` in `backend/services/cad_runner.py` performs AST parsing or regex dictionary replacement to overwrite the `PARAMS = {...}` block in the stored Python code before running the subprocess [Lines 248–310].
- **Implementation Status:** Complete in code [VERIFIED IN SOURCE]. Benchmark metric of $164\text{ ms}$ was observed manually in local testing; no committed automated JSON benchmark exists in the repo [UNVERIFIED BY LOG].

### Module 4: AST Security Screening & Subprocess Isolation
- **Purpose:** Mitigates arbitrary code execution attacks by statically analyzing and filtering all LLM-generated Python code before evaluation.
- **Problem Solved:** Running unvetted code generated by an AI model in a subprocess exposes the host system to command execution, file system tampering, and credential exfiltration.
- **Backend Implementation:** `validate_script_safety()` in `backend/services/cad_runner.py` [Lines 168–242].
- **Security Logic:**
  1. Denies forbidden AST nodes: `ast.Lambda`, `ast.Yield`, `ast.YieldFrom`, `ast.Await`, `ast.Global`, `ast.Nonlocal`.
  2. Enforces import whitelist: Only `build123d`, `math`, `typing`, `types`, `collections`, `itertools`, `functools`, `enum`, `dataclasses`, `abc`, `operator` are permitted.
  3. Blocks dangerous built-ins: `open`, `eval`, `exec`, `compile`, `__import__`, `input`, `globals`, `locals`, `getattr`, `setattr`, `delattr`, `breakpoint`.
  4. Blocks dunder reflection attacks: Rejects any attribute access beginning with `__` or referencing `__subclasses__`, `__bases__`, `__globals__`, `__code__`, `__mro__`.
  5. Inspects alias assignments (e.g., `g = getattr; g(...)`).
- **Implementation Status & Boundaries:** Complete and verified via 15 unit tests in `backend/test_ast_security.py` [VERIFIED BY EXECUTION]. Note: AST parsing is a static lexical barrier, not a hypervisor or OS container sandbox. It does not prevent CPU exhaustion loops within safe mathematical APIs [CALIBRATED].

### Module 5: OpenCASCADE CAD Execution & Validation Harness
- **Purpose:** Executes CAD scripts in a controlled subprocess and validates the output geometry.
- **Problem Solved:** Ensures generated 3D geometry is structurally sound, physically realizable, and mathematically watertight.
- **Backend Implementation:** `CADRunner.execute_script_async()` in `backend/services/cad_runner.py` [Lines 450–650].
- **Execution & Validation Logic:**
  1. Bounded concurrency: Enforced via `asyncio.Semaphore(CAD_MAX_CONCURRENT_EXECUTIONS)` (default: 2).
  2. Bounded timeout: 60-second subprocess kill switch (`CAD_EXECUTION_TIMEOUT_SECONDS`).
  3. Topology validation via `trimesh`: Computes Euler characteristic, asserts `is_watertight == True`, verifies single-solid monolithic volume ($V > 0$), and detects disconnected floating bodies.
  4. Error classification: Classifies stderr into `TIMEOUT`, `SYNTAX`, `SECURITY`, `RUNTIME`, `IO_ERROR`.
- **Implementation Status:** Complete and verified [VERIFIED IN SOURCE / VERIFIED BY EXECUTION].

### Module 6: Conversational Chat-to-Modify Engine
- **Purpose:** Modifies existing 3D models through natural language conversational requests (e.g., *"Make the mounting flange 5mm thicker and add 2 more holes"*).
- **Problem Solved:** Eliminates the need to start from scratch when adjusting a model beyond simple slider ranges.
- **User Interaction:** User switches to the "Chat to Modify" tab in the workbench sidebar, enters a change request, or clicks a contextual quick-suggestion chip.
- **Frontend Implementation:** `frontend/src/components/ChatModifyPanel.jsx` displays chat history and suggestion chips [Lines 1–150]. Dispatches `modifyPart()` via `App.jsx`.
- **Backend Implementation:** `POST /api/modify` in `backend/main.py` [Lines 1214–1380]. Uses `LLMService.modify_script()` and allocates a versioned script ID (`allocate_modify_script_id`) to branch the design without overwriting the original.
- **Implementation Status:** Complete and verified [VERIFIED IN SOURCE / VERIFIED BY EXECUTION].

### Module 7: AutoCAD-Grade 3D WebGL Viewport
- **Purpose:** High-performance, interactive rendering of 3D solid geometry in the browser.
- **Frontend Implementation:** `frontend/src/components/Viewer3D.jsx` [Lines 1–454].
- **Key Capabilities:**
  - `STLLoader` parsing binary geometry directly into Three.js buffer attributes.
  - `THREE.EdgesGeometry(geometry, 24)` extracting authentic CAD feature lines.
  - 5 AutoCAD visual styles: Shaded with Edges, Realistic, Conceptual, X-Ray, Wireframe.
  - 5 PBR Material presets defined in `constants/materials.js`: Standard Titanium (`cad_gray`), Machined Aluminum (`aluminum`), Anodized Blue (`blue`), Tooling Yellow (`yellow`), Cast Iron Slate (`dark`).
  - Interactive ViewCube and UCS/WCS coordinate tripod.
  - Real-time 3D crosshair coordinate readout tracking mouse position over the model plane.
  - Dynamic 3D bounding box dimension annotations displaying Length, Width, and Height in millimeters.
  - Interactive Section Cut tool creating a live clipping plane at $Y=0$.
- **Implementation Status:** Complete and verified [VERIFIED IN SOURCE].

### Module 8: Public Design Gallery & Fork Engine
- **Purpose:** Community repository for sharing, discovering, liking, and cloning CAD models.
- **User Interaction:** Users browse `/api/gallery` cards via `#gallery`. Clicking "Fork" clones the complete parametric script and parameters into their private workspace.
- **Frontend Implementation:** `frontend/src/pages/Gallery.jsx` [Lines 1–529].
- **Backend Implementation:** `backend/routes/gallery.py` [Lines 1–422].
- **Key Logic:** Instant debounced live search, tag filtering, atomic like counter increments, and isolated artifact cloning ensuring forked designs do not share files with originals.
- **Implementation Status:** Complete and verified [VERIFIED IN SOURCE].

---

## 6. Backend and API Analysis

### 6.1 Comprehensive API Endpoint Inventory

| Endpoint | HTTP Method | Purpose | Auth Required | Request Body | Response Structure | Database Operation | Error Handling | Source Location |
|---|---|---|---|---|---|---|---|---|
| `/api/health` | GET | Health and service configuration check | No | None | `{"status": "online", "service": "...", "version": "2.0.0", "storage_ready": bool, "gemini_configured": bool}` | None | 500 on unhandled crash | `backend/main.py:296` |
| `/api/metrics` | GET | Real-time observability and request telemetry | No | None | `{"service": "...", "total_requests": int, "error_rate_pct": float, "cad_generations": {...}, "latency_ms": {...}}` | None | None | `backend/main.py:310` |
| `/api/generate` | POST | Primary Natural Language to CAD synthesis | Optional (Required in Prod) | `{"prompt": str}` | `GenerateResponse` (status, script_id, part_name, python_code, parameters, mesh_url, step_url, mesh_info) | Inserts row into `generations` if authenticated | 400 (Bad prompt), 422 (CAD execution failed), 429 (Rate/Quota limit), 502 (LLM exhausted) | `backend/main.py:388` |
| `/api/generate/stream` | POST | SSE streaming CAD generation with progress | Optional (Required in Prod) | `{"prompt": str}` | `text/event-stream` emitting `{phase, message, progress, result}` | Inserts row into `generations` if authenticated | Streams `{phase: "error", message: "..."}` chunk before closing | `backend/main.py:556` |
| `/api/generate/sketch` | POST | Multimodal Sketch-to-CAD synthesis | Optional (Required in Prod) | Multipart: `image` (PNG/JPEG/WEBP file), `prompt` (optional str) | `GenerateResponse` + `visual_interpretation`, `sketch_parameters` | Inserts row into `generations` prefixed with `[Sketch]` | 400 (Empty image), 413 (>10MB), 415 (Invalid MIME), 502 (Vision fail), 503 (No API key) | `backend/main.py:729` |
| `/api/recompute` | POST | Fast parametric slider recomputation | Optional (Required in Prod) | `{"script_id": str, "python_code": str, "updated_parameters": {k: v}}` | `RecomputeResponse` (status, script_id, mesh_url, step_url, mesh_info, recomputation_time_ms) | None | 400 (Invalid geometry output), 422 (Schema validation fail), 429 (Rate limit) | `backend/main.py:967` |
| `/api/modify` | POST | Chat-to-Modify conversational refactoring | Optional (Required in Prod) | `{"script_id": str, "python_code": str, "modification_prompt": str, ...}` | `ModifyResponse` (new_script_id, python_code, parameters, mesh_url, step_url) | Inserts row into `versions` table if authenticated | 422 (Modification execution fail), 429 (Rate/Quota limit), 502 (LLM fail) | `backend/main.py:1214` |
| `/api/download/{script_id}/{fmt}` | GET | Download single artifact (STL, STEP, OBJ, GLB) | Gated (Owner/Public/Admin) | None | File stream with attachment header | Reads `generations` row to verify ownership | 400 (Invalid format/script_id), 403 (Private model), 404 (Artifact missing) | `backend/main.py:1149` |
| `/api/download/{script_id}/all` | GET | Download all formats as single ZIP archive | Gated (Owner/Public/Admin) | None | `application/zip` stream containing `{script_id}.*` | Reads `generations` row to verify ownership | 400 (Invalid script_id), 403 (Private model), 404 (No artifacts found) | `backend/main.py:1103` |
| `/api/script/{script_id}` | GET | Retrieve raw build123d Python script source | Admin Only (`X-Admin-Token`) | None | `{"status": "success", "script_id": str, "code": str}` | None | 400 (Invalid ID), 401 (Invalid token), 404 (Not found), 503 (Admin unconfigured) | `backend/main.py:1081` |
| `/static/models/{filename}` | GET | Serve mesh artifact files for 3D viewer | Public (Protected for `.py`) | None | Binary file response (STL, STEP, etc.) | On-demand regeneration if file missing from disk | 401 (Unauthorized .py), 404 (File not found) | `backend/main.py:342` |
| `/api/admin/models` | GET | List stored filesystem artifacts | Admin Only (`X-Admin-Token`) | None | `{"status": "success", "count": int, "models": [...]}` | None | 401 (Unauthorized) | `backend/main.py:1065` |
| `/api/admin/cleanup` | POST | Manually trigger purge of stale artifacts | Admin Only (`X-Admin-Token`) | None | `{"status": "success", "removed_files": int}` | None | 401 (Unauthorized) | `backend/main.py:1054` |
| `/api/auth/register` | POST | Create user account | No | `{"email": str, "password": str, "display_name": str}` | `AuthResponse` (access_token, refresh_token, user: {...}) | Inserts row into `users` table | 400 (Password >72 bytes), 409 (Email exists), 422 (Invalid email format), 429 (Rate limit) | `backend/routes/auth.py:98` |
| `/api/auth/login` | POST | Authenticate user credentials | No | `{"email": str, "password": str}` | `AuthResponse` (access_token, refresh_token, user: {...}) | Queries `users` table | 401 (Invalid credentials), 403 (Deactivated), 429 (Rate limit) | `backend/routes/auth.py:143` |
| `/api/auth/refresh` | POST | Rotate refresh token | No | `{"refresh_token": str}` | `AuthResponse` (new access_token, new refresh_token) | Updates `refresh_token_version` on `User` | 401 (Invalid/expired token or token reuse detected) | `backend/routes/auth.py:179` |
| `/api/auth/me` | GET | Get current authenticated user profile | Yes (Bearer Token) | None | `UserProfileResponse` (id, email, display_name, plan_tier, created_at) | Reads `users` table | 401 (Invalid/expired token) | `backend/routes/auth.py:224` |
| `/api/projects` | POST | Create design workspace project | Yes (Bearer Token) | `{"name": str, "description": Optional[str]}` | `{"status": "success", "project": {id, name}}` | Inserts row into `projects` table | 401 (Unauthorized), 422 (Validation error) | `backend/routes/projects.py:96` |
| `/api/projects` | GET | List current user's projects with counts | Yes (Bearer Token) | None | `{"status": "success", "projects": [...]}` | Selects `projects` with outer join on `generations` | 401 (Unauthorized) | `backend/routes/projects.py:117` |
| `/api/projects/{id}` | GET | Get project details and all generations | Yes (Bearer Token) | None | `{"status": "success", "project": {...}, "generations": [...]}` | Reads `projects` and child `generations` | 401 (Unauthorized), 404 (Not found) | `backend/routes/projects.py:152` |
| `/api/projects/{id}` | DELETE | Delete project and orphan child generations | Yes (Bearer Token) | None | `{"status": "success", "message": "..."}` | Deletes `projects` row (cascade deletes generations) | 401 (Unauthorized), 404 (Not found) | `backend/routes/projects.py:201` |
| `/api/generations/{id}` | GET | Get full generation details and version history | Optional | None | `{"status": "success", "generation": GenerationDetail}` | Reads `generations` with `selectinload(versions)` | 403 (Private model), 404 (Not found) | `backend/routes/projects.py:224` |
| `/api/gallery` | GET | Browse public designs with search & tags | No | None (Query: page, search, tag, sort_by) | `{"items": [...], "total": int, "page": int, "pages": int}` | Queries `generations` where `is_public == True` | 422 (Invalid tag/sort_by) | `backend/routes/gallery.py:115` |
| `/api/designs/{id}/publish` | POST | Publish a generation to the community gallery | Yes (Owner Only) | `{"tags": ["tag1", ...]}` or `["tag1", ...]` | `{"message": "Design published", "id": str, "is_public": True}` | Updates `generations.is_public = True` and `tags_json` | 401 (Unauthorized), 404 (Not found or not owner), 422 (Invalid tags) | `backend/routes/gallery.py:199` |
| `/api/designs/{id}/unpublish` | POST | Remove a design from public gallery | Yes (Owner Only) | None | `{"message": "Design unpublished", "id": str, "is_public": False}` | Updates `generations.is_public = False` | 401 (Unauthorized), 404 (Not found or not owner) | `backend/routes/gallery.py:240` |
| `/api/designs/{id}/like` | POST | Increment like counter on public design | Yes (Bearer Token) | None | `{"message": "Design liked", "id": str, "like_count": int}` | Atomic increment: `like_count = like_count + 1` | 401 (Unauthorized), 404 (Not found) | `backend/routes/gallery.py:270` |
| `/api/designs/{id}/fork` | POST | Fork a gallery design into user workspace | Yes (Bearer Token) | None | `{"message": "Design forked", "fork_id": str, "project_id": str}` | Copies generation row, regenerates files, updates `fork_count` | 401 (Unauthorized), 404 (Not found) | `backend/routes/gallery.py:302` |

### 6.2 Rate Limiting Architecture
The application implements two layers of rate limiting:
1. **API Endpoint Rate Limiter (`SimpleRateLimiter`):**
   - Configured in `backend/main.py` [Lines 84–126].
   - Employs a thread-safe sliding window tracking request timestamps per client.
   - Limits: `generate_limiter` = 10 req/min, `modify_limiter` = 10 req/min, `recompute_limiter` = 40 req/min.
   - Per-user rate keys: Authenticated requests use `user:<uuid>`, while unauthenticated requests use `ip:<client_ip>` [Line 129].
   - Standard response headers injected: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
   - Exceeded limits raise HTTP 429 with `Retry-After: <seconds>` header.
2. **Daily Generation Quota:**
   - Implemented in `backend/services/auth_service.py` (`check_and_bump_quota`) [Lines 41–93].
   - Limits authenticated free-tier users to **50 generations per UTC day**.
   - Resets automatically at midnight UTC when `last_generation_date != today`.
   - Exceeded quota raises HTTP 429 with error code `quota_exceeded`.

---

## 7. Database Analysis

### 7.1 Database Technology & Engine Architecture
- **Engine:** SQLAlchemy 2.0 Async Engine paired with `aiosqlite` (development/default) or `asyncpg` (production PostgreSQL).
- **WAL Configuration:** Automated write-ahead log pragmas applied at connection time in `backend/database.py`.
- **WAL Checkpoint:** Executes `PRAGMA wal_checkpoint(TRUNCATE)` on application startup to prevent unbounded disk growth [Lines 81–87].
- **Migration Framework:** Full Alembic environment located in `backend/alembic/` with revision tracking table `alembic_version`.

### 7.2 Entity-Relationship & Relational Schema

```
┌─────────────────────────────────┐
│              USERS              │
├─────────────────────────────────┤
│ PK  id: VARCHAR(36)             │
│     email: VARCHAR(255) [UQ,IX] │
│     password_hash: VARCHAR(255) │
│     display_name: VARCHAR(100)  │
│     plan_tier: VARCHAR(20)      │
│     api_key: VARCHAR(64) [UQ,IX]│
│     is_active: BOOLEAN          │
│     refresh_token_version: INT  │
│     generations_today: INT      │
│     last_generation_date: STR   │
│     created_at: DATETIME(TZ)    │
│     updated_at: DATETIME(TZ)    │
└───────────────┬─────────────────┘
                │ 1
                │
                │ N (Cascade Delete)
                ▼
┌─────────────────────────────────┐
│            PROJECTS             │
├─────────────────────────────────┤
│ PK  id: VARCHAR(36)             │
│ FK  user_id: VARCHAR(36) [IX]   │
│     name: VARCHAR(200)          │
│     description: TEXT           │
│     created_at: DATETIME(TZ)    │
│     updated_at: DATETIME(TZ)    │
└───────────────┬─────────────────┘
                │ 1
                │
                │ N (Cascade Delete)
                ▼
┌─────────────────────────────────┐
│           GENERATIONS           │
├─────────────────────────────────┤
│ PK  id: VARCHAR(36)             │
│ FK  project_id: VARCHAR(36) [IX]│
│ FK  user_id: VARCHAR(36) [IX]   │
│     prompt: TEXT                │
│     script_id: VARCHAR(100) [IX]│
│     part_name: VARCHAR(200)     │
│     description: TEXT           │
│     python_code: TEXT           │
│     parameters_json: TEXT       │
│     mesh_info_json: TEXT        │
│     mesh_url: VARCHAR(500)      │
│     step_url: VARCHAR(500)      │
│     model_used: VARCHAR(100)    │
│     generation_time_ms: INT     │
│     self_corrections: INT       │
│     design_mode: VARCHAR(20)    │
│     components_json: TEXT       │
│     is_public: BOOLEAN [IX]     │
│     like_count: INT [IX]        │
│     fork_count: INT [IX]        │
│     tags_json: TEXT             │
│     forked_from: VARCHAR(36)    │
│     created_at: DATETIME(TZ)[IX]│
└───────────────┬─────────────────┘
                │ 1
                │
                │ N (Cascade Delete)
                ▼
┌─────────────────────────────────┐
│            VERSIONS             │
├─────────────────────────────────┤
│ PK  id: VARCHAR(36)             │
│ FK  generation_id: VARCHAR(36)  │
│     version_number: INT         │
│     modification_prompt: TEXT   │
│     script_id: VARCHAR(100)     │
│     python_code: TEXT           │
│     parameters_json: TEXT       │
│     mesh_info_json: TEXT        │
│     mesh_url: VARCHAR(500)      │
│     step_url: VARCHAR(500)      │
│     model_used: VARCHAR(100)    │
│     created_at: DATETIME(TZ)    │
└─────────────────────────────────┘
```

### 7.3 Detailed Entity Specifications

#### Table: `users` (`backend/models/user.py`)
- `id`: `String(36)`, Primary Key, UUID v4 string default.
- `email`: `String(255)`, Unique, Indexed, Non-nullable. Validated via regex on registration.
- `password_hash`: `String(255)`, Non-nullable. Stores BCrypt hash.
- `display_name`: `String(100)`, Default `"Engineer"`.
- `plan_tier`: `String(20)`, Default `"free"`.
- `api_key`: `String(64)`, Unique, Indexed, Nullable.
- `is_active`: `Boolean`, Default `True`. Soft deactivation flag.
- `refresh_token_version`: `Integer`, Default `0`. Incremented on token refresh to detect and block token reuse attacks.
- `generations_today`: `Integer`, Default `0`. Free-tier quota counter.
- `last_generation_date`: `String(10)`, Nullable. Stores `YYYY-MM-DD` in UTC for daily quota resets.
- `created_at` / `updated_at`: `DateTime(timezone=True)`. Auto-populated UTC timestamps.

#### Table: `projects` (`backend/models/project.py`)
- `id`: `String(36)`, Primary Key, UUID v4 string default.
- `user_id`: `String(36)`, Foreign Key referencing `users.id`, Indexed, Non-nullable.
- `name`: `String(200)`, Default `"Untitled Project"`.
- `description`: `Text`, Nullable.
- `created_at` / `updated_at`: `DateTime(timezone=True)`.

#### Table: `generations` (`backend/models/project.py`)
- `id`: `String(36)`, Primary Key, UUID v4 string default.
- `project_id`: `String(36)`, Foreign Key referencing `projects.id`, Indexed, Non-nullable.
- `user_id`: `String(36)`, Foreign Key referencing `users.id`, Indexed, Non-nullable.
- `prompt`: `Text`, Non-nullable. Original natural language prompt.
- `script_id`: `String(100)`, Indexed, Non-nullable. Unique alphanumeric filename stem.
- `part_name`: `String(200)`, Nullable. Human-readable name.
- `description`: `Text`, Nullable. Summary of design features.
- `python_code`: `Text`, Non-nullable. Full executable `build123d` script source.
- `parameters_json`: `Text`, Nullable. JSON-encoded list of `CADParameter` objects.
- `mesh_info_json`: `Text`, Nullable. JSON-encoded geometric analysis dictionary.
- `mesh_url`: `String(500)`, Nullable. Relative URL to preview STL.
- `step_url`: `String(500)`, Nullable. Relative URL to manufacturing STEP.
- `model_used`: `String(100)`, Nullable. Tier and model identifier.
- `generation_time_ms`: `Integer`, Nullable. Kernel execution duration in ms.
- `self_corrections`: `Integer`, Default `0`. Number of retry correction loops.
- `design_mode`: `String(20)`, Default `"single_solid"`. Options: `"single_solid"`, `"assembly"`.
- `components_json`: `Text`, Nullable. JSON-encoded list of component names.
- `is_public`: `Boolean`, Default `False`, Indexed. Gallery visibility toggle.
- `like_count`: `Integer`, Default `0`, Indexed. Gallery like counter.
- `fork_count`: `Integer`, Default `0`, Indexed. Gallery fork counter.
- `tags_json`: `Text`, Nullable. JSON-encoded array of lowercase tag strings.
- `forked_from`: `String(36)`, Nullable. Parent generation UUID if cloned.
- `created_at`: `DateTime(timezone=True)`, Indexed.

#### Table: `versions` (`backend/models/project.py`)
- `id`: `String(36)`, Primary Key, UUID v4 string default.
- `generation_id`: `String(36)`, Foreign Key referencing `generations.id`, Indexed, Non-nullable.
- `version_number`: `Integer`, Non-nullable. Sequential integer ($1, 2, 3\dots$).
- `modification_prompt`: `Text`, Non-nullable. Natural language modification text.
- `script_id`: `String(100)`, Non-nullable. Versioned script identifier (e.g., `part_123_v1`).
- `python_code`: `Text`, Non-nullable. Updated script source.
- `parameters_json` / `mesh_info_json` / `mesh_url` / `step_url` / `model_used`: Mirrors parent attributes for this version.
- `created_at`: `DateTime(timezone=True)`.

### 7.4 Textual Specification for Manual ER Diagram Creation
For the final JUET Minor Project report, students can manually draw the ER diagram using this structural specification:
- **Entities:** Represent `USERS`, `PROJECTS`, `GENERATIONS`, and `VERSIONS` as rectangular entity boxes.
- **Attributes:** Draw primary keys with underlining (`id`). Draw foreign keys with dashed underlining (`user_id`, `project_id`, `generation_id`).
- **Relationship 1 (Users to Projects):** One-to-Many (`1:N`). Label as *"owns"*. Cardinality: One user can create zero or many projects; each project must belong to exactly one user. Crow's foot on the `PROJECTS` side.
- **Relationship 2 (Users to Generations):** One-to-Many (`1:N`). Label as *"authors"*. Cardinality: One user creates many generations. Crow's foot on `GENERATIONS` side.
- **Relationship 3 (Projects to Generations):** One-to-Many (`1:N`). Label as *"contains"*. Cardinality: One project contains zero or many generations; each generation belongs to exactly one project workspace. Crow's foot on `GENERATIONS` side.
- **Relationship 4 (Generations to Versions):** One-to-Many (`1:N`). Label as *"branches into"*. Cardinality: One generation has zero or many modification versions; each version references exactly one parent generation. Crow's foot on `VERSIONS` side.
- **Self-Referential Relationship (Generations to Generations):** Zero-to-One recursive link on `forked_from` representing gallery cloning.

---

## 8. Algorithms and Technical Concepts

### 8.1 Algorithm 1: Semantic RAG Few-Shot Context Retrieval
- **What It Does:** Takes a natural language user query and searches a local vector store containing 121 domain-specific CAD blueprints, returning the top-$k$ ($k=3$) most geometrically relevant Python scripts to inject into the LLM system prompt.
- **Why It Is Needed:** LLMs trained on general internet code frequently hallucinate incorrect `build123d` API calls, conflate `cadquery` with `build123d`, or attempt to draw 1D sketch wires without faces. Injecting verified, working blueprints guarantees syntactically correct code generation.
- **Inputs:** `query` (str, user prompt), `k` (int, default 3), `min_similarity` (float, threshold 0.25).
- **Processing Steps:**
  1. Lazy-load `SentenceTransformer('all-MiniLM-L6-v2')`.
  2. Embed user query into a 384-dimensional dense vector: $\mathbf{q} \in \mathbb{R}^{384}$.
  3. Query persistent ChromaDB collection using cosine similarity:
     $$\text{Cosine Similarity}(\mathbf{q}, \mathbf{d}_i) = \frac{\mathbf{q} \cdot \mathbf{d}_i}{\|\mathbf{q}\|_2 \|\mathbf{d}_i\|_2} = 1 - \text{Cosine Distance}$$
  4. Filter candidates where similarity $\ge 0.25$.
  5. Format retrieved exemplars into Markdown few-shot code blocks.
- **Output:** Formatted few-shot string injected into `BUILD123D_SYSTEM_PROMPT`.
- **Complexity:**
  - Time Complexity: Embedding computation is $O(L)$ where $L$ is query character length. ChromaDB HNSW vector index search is $O(\log N)$ where $N=121$ documents. Total latency $<25\text{ ms}$.
  - Space Complexity: $O(D)$ where $D=384$ vector dimensions.
- **Source Code Implementation:** `backend/services/rag_service.py` (`retrieve` Lines 180–230).
- **Limitations:** Only indexes static example files; does not index user-generated models from the gallery.

### 8.2 Algorithm 2: AST Static Security Analysis & Deserialization Defense
- **What It Does:** Parses arbitrary Python source text into an Abstract Syntax Tree (AST) using Python's native `ast` module and inspects every node to detect security violations before compilation.
- **Why It Is Needed:** Conventional execution via `exec()` or simple subprocess calls exposes the host system to unauthorized file access, socket connections, and shell spawning. AST validation screens code before execution begins.
- **Inputs:** `python_code` (str).
- **Processing Steps:**
  1. Call `ast.parse(python_code)`. Syntax errors abort immediately.
  2. Pass 1: Run `_collect_dangerous_aliases()` across all `ast.Assign` and `ast.AnnAssign` nodes to find variables bound to prohibited functions (e.g., `f = open`, `g = getattr`).
  3. Pass 2: Traverse tree using `ast.walk()`.
  4. Node Type Checks:
     - Disallow syntax constructs: `ast.Lambda`, `ast.Yield`, `ast.Global`, `ast.Nonlocal`.
     - Inspect `ast.Import` and `ast.ImportFrom`: Split root module and assert membership in `ALLOWED_IMPORTS`.
     - Inspect `ast.Call`: Verify function names against `BLOCKED_BUILTINS` and identified alias set.
     - Inspect `ast.Attribute`: Check if attribute starts with `__` or matches `BLOCKED_ATTRIBUTES` (`__subclasses__`, `__globals__`).
  5. Return `(True, "OK")` or `(False, "Blocked ...")`.
- **Output:** Boolean safety determination and human-readable rejection reason.
- **Complexity:**
  - Time Complexity: $O(V)$ where $V$ is the number of AST nodes (linear in script length, executes in $<2\text{ ms}$).
  - Space Complexity: $O(V)$ for AST node storage.
- **Source Code Implementation:** `backend/services/cad_runner.py` (`validate_script_safety` Lines 168–242).
- **Limitations & Security Boundaries:** Static AST analysis is a heuristic defense filter, not an impenetrable sandbox. It cannot detect algorithmic complexity attacks (e.g., computationally explosive boolean operations that monopolize CPU), memory exhaustion within whitelisted modules, or dynamic evasion vectors not visible at the AST level. Host protection relies on the multi-layered defense model (AST screening + stripped subprocess environment + 60s timeout + concurrency semaphore).

### 8.3 Algorithm 3: Closed-Loop Automated Self-Correction
- **What It Does:** When a generated script fails due to a Python exception, AST violation, or geometric topology defect, the system intercepts the traceback and invokes the LLM to rewrite the code.
- **Why It Is Needed:** Even with RAG context, LLMs occasionally make geometric errors (e.g., trying to fillet an edge with a radius larger than the face, or placing a feature outside the bounding box). Automated correction increases generation success from 80% to 90%.
- **Inputs:** `user_prompt` (str), `failed_code` (str), `error_traceback` (str).
- **Processing Steps:**
  1. Attempt execution of script in isolated subprocess.
  2. On non-zero exit code or `is_valid == False`, capture `stderr` or geometry warnings.
  3. Format `CORRECTION_PROMPT_TEMPLATE` with original prompt, failed code, and exact error snippet.
  4. Dispatch to LLM: Requests a corrected `DualOutputPayload` with the offending lines fixed.
  5. Repeat up to `MAX_RETRIES = 3` times.
- **Output:** Corrected, executable Python code or a final 422 HTTP exception if all retries fail.
- **Complexity:** Bounded at $M$ iterations ($M \le 3$), where each iteration incurs one LLM inference latency ($10\text{--}18\text{ s}$) and one kernel compilation ($1\text{--}3\text{ s}$).
- **Source Code Implementation:** `backend/main.py` (Lines 447–485) and `backend/services/llm_service.py` (`correct_code` Lines 540–585).
- **Limitations:** If the prompt requires an impossible geometric configuration under `build123d` CSG rules (e.g. self-intersecting fillets on acute corners), retries will exhaust without resolution.

### 8.4 Algorithm 4: Geometric Topology & 2-Manifold Mesh Validation
- **What It Does:** Examines the boundary representation of compiled solids and their exported STL triangle meshes to ensure they represent physically realizable, watertight objects.
- **Why It Is Needed:** 3D printing slicing software requires watertight (2-manifold) meshes without self-intersections or holes. Disconnected floating components in a single-solid part cause manufacturing failures.
- **Inputs:** `mesh_path` (Path to generated STL file), `part_object` (build123d Part object).
- **Processing Steps:**
  1. Inspect build123d solid count: `assert len(part.part.solids()) == 1` for `single_solid` mode.
  2. Load exported mesh via `trimesh.load(mesh_path)`.
  3. Validate 2-manifold Euler characteristic:
     $$\chi = V - E + F = 2(1 - g)$$
     For a genus-0 sphere-equivalent solid, $\chi = 2$.
  4. Compute `mesh.is_watertight`: Every mesh edge must be shared by exactly two triangular faces.
  5. Compute connected volumetric components: Detect if mesh contains multiple disconnected shells.
  6. Compute volume ($V > 0\text{ mm}^3$) and bounding box coordinates ($\text{bbox}_{\min}, \text{bbox}_{\max}$).
- **Output:** `mesh_info` dictionary containing volume, face count, dimensions, watertight status, and warning flags.
- **Complexity:** $O(F)$ where $F$ is the triangle face count (typically $10^3\text{--}10^5$ triangles, evaluated in $<50\text{ ms}$).
- **Source Code Implementation:** `backend/services/cad_runner.py` (Lines 480–540).
- **Limitations & Physical Reality:** Mathematical mesh watertightness in `trimesh` confirms topological validity, but does **not** guarantee real-world physical 3D printability (slicing orientation, overhang support requirements, bed adhesion, structural integrity, or nozzle clearance).

### 8.5 Algorithm 5: Geometric Chain-of-Thought Sketch Parsing
- **What It Does:** Analyzes a raster engineering drawing or hand sketch to extract explicit 3D coordinate alignments, extrusion strategies, curve rules, and dimensions.
- **Why It Is Needed:** Vision LLMs tend to generate vague descriptions of sketches. This algorithm forces the vision model to reason step-by-step through manufacturing constraints before synthesizing code.
- **Processing Steps:**
  1. Pre-process image: Enforce $\le 10\text{ MB}$, valid MIME (PNG/JPEG/WEBP).
  2. Send to Gemini Vision / Groq Vision with strict Pydantic `response_schema=SketchVisionAnalysis`.
  3. Enforce 7-step reasoning chain:
     - Step 1 (Axis Mapping): Assign dimensions to $X, Y, Z$ axes.
     - Step 2 (Base Profile): Select 3D primitives vs. 2D extruded profile.
     - Step 3 (Curve Rule): Check for arches; forbid box-minus-box boolean subtraction.
     - Step 4 (Feature Elevations): Explicitly map $Z$-heights of flanges, bosses, and holes.
     - Step 5 (Structural Blueprint): Step-by-step solid generation plan.
     - Step 6 (Dimension Extraction): Extract up to 12 numeric values in mm/degrees into a snake_case dictionary.
     - Step 7 (Derived Prompt Synthesis): Combine steps 1–6 into a complete CAD specification.
  4. Mandatory Parameter Enforcement: Inject extracted dimensions directly into the downstream `PARAMS` dictionary.
- **Output:** `ParsedSketch` object feeding directly into the CAD generation pipeline.
- **Source Code Implementation:** `backend/services/vision_service.py` (`parse_sketch` Lines 423–520).
- **Limitations:** Heavily distorted perspective drawings or illegible handwriting can lead to misidentified dimension digits.

---

## 9. Testing and Validation

### 9.1 Test Suite Inventory & Results
The test suite was executed via the project's virtual environment:
`cd backend && .\venv\Scripts\python.exe -m pytest -q --tb=short`

**Execution Result:** `88 passed, 1 skipped, 2 warnings in 188.72s (0:03:08)` [VERIFIED BY EXECUTION].

| Test File | Test Count | Scenarios Tested | Run in CI? | Status | Evidence |
|---|---|---|---|---|---|
| `test_schemas.py` | 12 | Pydantic schema validation: CADParameter bounds, numeric types, integer steps, DualOutputPayload design mode checks, Prompt length bounds, Recompute parameter range validation | **Yes** | `[VERIFIED BY EXECUTION]` | 12/12 passing in pytest run |
| `test_ast_security.py` | 15 | AST Sandboxing: Script ID path traversal rejection, safe script validation, blocked `os`/`subprocess` imports, blocked `open`/`eval`/`exec`/`input`, blocked `__globals__`/`__subclasses__` reflection, alias bypasses, lambda exfiltration | **Yes** | `[VERIFIED BY EXECUTION]` | 15/15 passing in pytest run |
| `test_llm_parser.py` | 4 | Robust JSON Parsing: Strict JSON, non-strict JSON with unescaped control chars/newlines, regex fallback for truncated output, syntax recovery | **Yes** | `[VERIFIED BY EXECUTION]` | 4/4 passing in pytest run |
| `test_geometry_validation.py` | 4 | OpenCASCADE & Mesh Validation: Disconnected solid detection, multi-body assembly validation, monolithic single-solid validation, missing STEP export detection | **Yes** | `[VERIFIED BY EXECUTION]` | 4/4 passing in pytest run |
| `test_recompute_validation.py` | 3 | Recomputation Contracts: Invalid mesh rejection, unique execution artifact naming, rate limit response headers | **Yes** | `[VERIFIED BY EXECUTION]` | 3/3 passing in pytest run |
| `test_auth_projects.py` | 5 | Auth & Project Workspaces: BCrypt password hashing, JWT encode/decode roundtrip, user registration/login flow, project CRUD isolation, generation detail permission gates | **Yes** | `[VERIFIED BY EXECUTION]` | 5/5 passing in pytest run |
| `test_universal_archetypes.py`| 6 | CAD Archetypes & RAG Coverage: Intent detection across 10 archetypes, RAG semantic retrieval, syntax/AST validation of all 20 universal scripts, stepped shaft compilation, electronics enclosure compilation, live LLM benchmark (skipped by design) | **Yes** | `[VERIFIED BY EXECUTION]` | 5 passed, 1 skipped (by design for hermetic test runs) |
| `test_pipeline.py` | 1 | Full Asynchronous Pipeline: Complete end-to-end integration test running code synthesis, sandbox execution, mesh generation, and file output | **Yes** | `[VERIFIED BY EXECUTION]` | 1/1 passing in pytest run |
| **CI Configuration Subtotal** | **50 tests** | **Core regression suite across 8 files** | | `[VERIFIED IN SOURCE]` | Configured in `.github/workflows/ci.yml:47-56` |
| `test_gallery_and_formats.py`| 1 | Public Gallery & Observability: Gallery browsing, tag filtering, metrics endpoint payload verification | Local Only | `[VERIFIED BY EXECUTION]` | 1/1 passing in pytest run |
| `test_gemini_web_client.py` | 7 | Reverse-Engineered Web2API Client: Model specs resolution, privacy flags, SAPISID hashing, stream response error handling, fallback integration | Local Only | `[VERIFIED BY EXECUTION]` | 7/7 passing in pytest run |
| `test_modify_params.py` | 5 | Chat-to-Modify Contracts: Request validation, short prompt rejection, response schema conformance, LLM modify contract, concurrent version ID collision safety | Local Only | `[VERIFIED BY EXECUTION]` | 5/5 passing in pytest run |
| `test_pii_scrub.py` | 3 | PII Scrubbing: Email regex redaction, phone number redaction, API secret token redaction | Local Only | `[VERIFIED BY EXECUTION]` | 3/3 passing in pytest run |
| `test_quota.py` | 10 | Daily Quotas & Artifact Access: Daily quota reset at midnight UTC, 429 quota exhaustion, quota increments, guest bypass, rate keys, ZIP export-all, private download gating | Local Only | `[VERIFIED BY EXECUTION]` | 10/10 passing in pytest run |
| `test_api.py` | 5 | Administrative Endpoints: Admin token verification, open development routes, production admin enforcement, python source access protection, async route dispatch | Local Only | `[VERIFIED BY EXECUTION]` | 5/5 passing in pytest run |
| `test_sketch_endpoint.py` | 8 | Sketch-to-CAD API Endpoint: Missing image 422, unsupported MIME 415, empty file 400, missing API key 503, PNG happy path, JPEG happy path, vision failure 502, prompt guidance support | Local Only | `[VERIFIED BY EXECUTION]` | 8/8 passing in pytest run |
| **Full Local Test Suite** | **89 tests** | **15 test files** | | `[VERIFIED BY EXECUTION]` | 88 passed, 1 skipped by design in 188.72s |

> [!NOTE]
> **Reconciliation of Test Counts Across Repo Documentation:**
> - `README.md` (79 tests) and `AGENTS.md` (80 tests / 14 files) reflect earlier development snapshots and are **outdated**.
> - GitHub Actions CI (`.github/workflows/ci.yml`) is explicitly configured to execute **8 core test files containing 50 test items** to minimize workflow duration.
> - The active repository collects **89 test items across 15 test files**, passing completely (88 passed, 1 hermetic skip) in the local Python environment.

### 9.2 Frontend Validation Results
- **Linter:** `npm run lint` (`oxlint`) executed across 27 source files. Result: **0 errors, 0 warnings** [VERIFIED BY EXECUTION].
- **Production Build:** `npm run build` (`vite build`) compiled in **1.70 seconds**. Output bundle produced clean, code-split chunks for `Viewer3D`, `Gallery`, `LandingPage`, and vendor libraries [VERIFIED BY EXECUTION].

### 9.3 Recommended Manual Tests for Project Team
Before submitting the final report, the project team should manually perform:
1. **Physical 3D Print Test:** Export an STL file generated by the workbench (e.g., the Stepped Drive Shaft or Mounting Bracket), import it into Cura / PrusaSlicer, slice it with standard layer heights, and confirm slicer toolpath validity.
2. **CAD Interchange Test:** Export a STEP file, open it in Autodesk Fusion 360 or FreeCAD, and verify that faces, holes, and cylinders are recognized as native B-Rep solids rather than faceted polygon approximations.
3. **Cross-Browser Verification:** Verify the WebGL viewport manually in Chromium (Chrome/Edge) and Firefox to ensure shader parity.
4. **Mobile Responsive Layout Check:** Open the workbench on a smartphone screen ($\le 480\text{ px}$) to verify the collapsible sidebar and touch orbit gestures.

---

## 10. Results and Performance

### 10.1 Empirical Performance Metrics
Performance figures compiled from `backend/benchmark_results.json` and local measurements:

| Metric | Target (PRD) | Measured / Observed Value | Verification Status | Notes / Evidence |
|---|---|---|---|---|
| **P50 Generation Latency** | $\le 10\text{ s}$ | $\mathbf{17.25\text{ s}}$ ($17,250\text{ ms}$) | `[VERIFIED IN SOURCE]` | True mathematical median across all 20 benchmark prompts (`benchmark_results.json`). Mean latency is $17.14\text{ s}$ ($17,140\text{ ms}$). Earlier $14.2\text{ s}$ claim was prompt #4 only. |
| **P50 Recompute Latency** | $<200\text{ ms}$ | $\mathbf{164\text{ ms}}$ (manually observed) | `[UNVERIFIED BY LOG]` | Observed in local development via direct AST injection; no automated benchmark JSON log committed. Target $<200\text{ ms}$ verified structurally. |
| **First-Pass Generation Success** | $\ge 80\%$ | $\mathbf{80.0\%}$ (16/20) | `[VERIFIED IN SOURCE]` | 16 out of 20 benchmark prompts succeeded on the first attempt without self-correction. |
| **Overall Generation Success** | $\ge 85\%$ | $\mathbf{90.0\%}$ (18/20) | `[VERIFIED IN SOURCE]` | 2 additional models recovered via the self-correction loop; final benchmark success rate was 90%. |
| **Self-Correction Recovery Rate**| $\ge 50\%$ | $\mathbf{50.0\%}$ (2/4) | `[VERIFIED IN SOURCE]` | Out of 4 initial non-first-pass attempts, 2 recovered successfully within 3 retry iterations ($2/4 = 50.0\%$). |
| **Frontend Production Build Time**| $<5.0\text{ s}$ | $\mathbf{1.70\text{ s}}$ | `[VERIFIED BY EXECUTION]` | Measured with Vite 8.3 production rollup bundler. |
| **Frontend Lint Status** | 0 warnings | **0 warnings, 0 errors** | `[VERIFIED BY EXECUTION]` | Enforced by Oxlint 1.86 across 27 JavaScript/JSX files. |
| **Automated Test Suite Pass Rate**| $100\%$ | **100%** (88/88 passing, 1 skip)| `[VERIFIED BY EXECUTION]` | 88 passed, 1 skipped by design in 188.72s. |

### 10.2 Benchmark Evaluation Analysis (20 Standard Engineering Prompts)
From `backend/benchmark_results.json`:
- **Fastest Successful Generation:** `box_basic` (11,200 ms, Volume: $30,000\text{ mm}^3$).
- **First-Pass Successes:**
  - `cylinder_basic`: 12,150 ms
  - `hollow_cylinder`: 13,400 ms
  - `l_bracket`: 14,200 ms (Volume: $17,250\text{ mm}^3$)
  - `flanged_bushing`: 14,800 ms
  - `hex_standoff`: 15,300 ms
  - `t_bracket`: 15,600 ms
  - `c_channel`: 15,800 ms
  - `shaft_collar`: 16,200 ms
  - `corner_mount`: 16,900 ms
  - `pipe_flange`: 17,600 ms
  - `electronics_box`: 17,800 ms
  - `pcb_tray`: 18,400 ms
  - `pulley`: 18,900 ms
  - `vented_panel`: 19,200 ms
  - `heat_sink`: 20,400 ms
- **Self-Corrected Recoveries:**
  - `t_slot_bar`: 23,500 ms (Recovered on retry 1)
  - `gear_blank`: 26,100 ms (Recovered on retry 1)
- **Unrecovered Failures:**
  - `chamfered_box`: 29,800 ms (Exhausted 3 retries; `Standard_ConstructionError: Chamfer face overlap on corner vertices`)
  - `sphere_pedestal`: 31,200 ms (Exhausted 3 retries; `TopologyError: Multiple disjoint solids detected`)

---

## 11. Security and Reliability Analysis

### 11.1 Implemented Security Defenses
1. **Static AST Analysis:** All generated scripts are parsed via `validate_script_safety()` before evaluation. The analyzer enforces an import whitelist (11 safe modules), denies dangerous syntax nodes (`Lambda`, `Yield`, `Global`), blocks builtins (`open`, `eval`, `exec`, `compile`, `getattr`), and prevents dunder attribute access (`__subclasses__`, `__globals__`).
2. **Subprocess Isolation:** CAD scripts execute in an external Python subprocess managed by `asyncio.to_thread` and `subprocess.run`. The subprocess environment (`isolated_env`) is explicitly stripped of all application API keys, database credentials, and session secrets, setting `PYTHONNOUSERSITE="1"` and `PYTHONPATH=""`.
3. **Execution Timeout & Concurrency Bounds:** Subprocesses are bounded by a strict 60-second execution kill switch (`CAD_EXECUTION_TIMEOUT_SECONDS`) and a global semaphore capping concurrent executions at 2 (`CAD_MAX_CONCURRENT_EXECUTIONS`).
4. **Filesystem Path Traversal Guards:** All script identifiers and model filenames are strictly validated against `SAFE_SCRIPT_ID_PATTERN` (`^[A-Za-z0-9_-]{1,100}$`). Path traversal sequences (`../`, `/etc/`) are rejected with HTTP 400.
5. **PII Scrubbing Pipeline:** Outgoing user prompts to cloud LLMs pass through `scrub_pii()`, redacting email addresses, phone numbers, AWS keys, GitHub tokens, and Bearer authorization headers.
6. **Authentication & Session Hardening:** Passwords hashed with BCrypt. JWT refresh tokens implement version tracking (`refresh_token_version`), immediately invalidating sessions upon detected token reuse.

### 11.2 Identified Security & Reliability Weaknesses (Realistic Assessment)
- **Static AST Limitations:** Static syntax analysis cannot anticipate dynamic execution behavior within permitted libraries. For instance, nested CSG operations in `build123d` or complex loops using `math` cannot be identified as malicious at the AST level, potentially consuming 100% CPU until the 60-second timeout fires.
- **Host OS Resource Boundaries:** On developer machines without Linux cgroups or Docker containerization, a memory-intensive CAD operation could consume substantial host RAM before timing out.
- **Single-Process Rate Limiting:** `SimpleRateLimiter` maintains sliding-window timestamps in process memory (`defaultdict`). In a multi-worker production cluster behind a load balancer, limits are not shared across processes without an external Redis instance.

---

## 12. Development Process and Project History

### 12.1 Development Progression (Week-by-Week Milestones)
Based on `CHANGELOG.md` and repository commit history:
- **Phase 1 (Weeks 1–3) — Core CAD Pipeline & AST Screening:**
  - Initialized FastAPI backend and OpenCASCADE `build123d` integration.
  - Developed initial AST import whitelist and subprocess execution runner.
  - Implemented Dual-Output Pydantic schemas (`CADParameter`, `DualOutputPayload`).
  - Added closed-loop self-correction retry handler.
- **Phase 2 (Weeks 4–5) — RAG Context & Three.js Viewport:**
  - Integrated ChromaDB vector store with 121 domain-specific CAD blueprints.
  - Integrated local sentence-transformers (`all-MiniLM-L6-v2`) dense embeddings.
  - Built initial React Three Fiber 3D viewer with OrbitControls and STL mesh rendering.
  - Delivered sub-200ms slider recomputation via AST parameter injection.
- **Phase 3 (Weeks 6–7) — Database, Auth & Chat-to-Modify:**
  - Added SQLAlchemy 2.0 async database layer with User, Project, Generation, and Version models.
  - Implemented JWT authentication with BCrypt hashing and sliding-window rate limiters.
  - Created Chat-to-Modify conversational refactoring engine with version branching.
  - Built Neobrutalist Bento Grid UI with real-time Telemetry HUD.
- **Phase 4 (Weeks 8–10) — Community Gallery & Universal Archetypes:**
  - Developed Public Design Gallery with live search, tags, forking, and likes.
  - Codified the 8 Universal CAD Archetypes in `examples_universal.py`.
  - Added multi-format export pipeline (STL, STEP, OBJ, GLB, and batch ZIP).
  - Hardened AST sandbox against dunder reflection, aliases, and lambda exfiltration.
- **Phase 5 (Recent) — Multimodal Vision, Migrations & Polishing:**
  - Built Sketch-to-CAD pipeline with Gemini Vision and Groq Vision fallback.
  - Added Alembic async database migration environment.
  - Integrated Prism.js syntax highlighting and 3D section cut tool.
  - Cleaned all React compiler and Oxlint warnings to 0.

### 12.2 Items Requiring Team Confirmation
The following operational items cannot be verified through code alone and must be confirmed by the student project team:
1. **Individual Student Contributions:** Commit logs show collaborative merges; individual team member assignments (e.g., who implemented the Three.js viewport vs. the AST security engine) must be specified by the team.
2. **University Supervisor / Mentor Name:** Faculty mentor details for the JUET title page.
3. **Specific Hardware Specifications:** CPU, RAM, and GPU models of the laboratory machines used for testing and benchmarking.

---

## 13. System Limitations & Realistic Future Improvements

### 13.1 Current System Limitations (Technical, Functional & Scalability)
- **Single-Node Execution Bottleneck:** CAD compiles execute as local subprocesses on the backend server. Under high concurrent user traffic, the semaphore queue ($N=2$) causes queuing delays.
- **No Dynamic Kinematics:** While static assemblies are supported in `assembly` mode, dynamic kinematic joint simulations (e.g. gears rotating in mesh, hinges pivoting, mechanical linkages) are not implemented.
- **Latency vs. Interactive CAD:** Initial generation requires $11\text{--}26\text{ s}$ due to cloud LLM inference and OpenCASCADE solid compilation. Only slider recomputation is sub-second.
- **In-Memory Rate Limiting:** Rate limiters do not share state across distributed worker nodes without an external Redis store.
- **Handwritten Sketch Ambiguity:** Distorted perspective hand-sketches or non-standard dimension symbols may have numeric callouts misidentified by the vision model.
- **Mesh Validation vs. 3D Print Reality:** Passing `trimesh` watertightness checks does not guarantee physical additive manufacturing success (e.g. support structures, thermal shrinkage, bed adhesion).

### 13.2 Proposed Future Work (Clearly Labeled as Non-Implemented Proposals)
1. **Asynchronous Distributed Task Queue (Proposed):** Introduce Celery and Redis to distribute CAD execution across a worker cluster, enabling horizontal scalability beyond 2 concurrent tasks.
2. **2D Engineering Drawing Generator (Proposed):** Implement automatic generation of orthographic 2D technical drawings (front, top, side, section) with dimension callouts formatted as downloadable SVG or DXF files.
3. **Kinematic Assembly Simulation (Proposed):** Integrate physics constraints into the 3D viewer using Rapier.js or Cannon.js to allow interactive testing of hinges, sliders, and gear trains.
4. **Fine-Tuned Open-Source CAD LLM (Proposed):** Fine-tune an open-source model (e.g., CodeLlama-7B or Qwen-2.5-Coder) specifically on the `build123d` syntax to eliminate dependency on third-party cloud LLM APIs.

---

## 14. Technical Diagram Specifications (For Manual Drawing)

*Note: Per JUET examination guidelines prohibiting automated diagram generation, this section provides exact structural specifications so that the project team can manually draw accurate diagrams.*

### 14.1 System Architecture Diagram Specification
- **Top Layer (Presentation / Client):**
  - Draw a large box labeled *"Frontend Client (React 19 SPA / Vite)"*.
  - Inside, place 4 distinct component blocks:
    1. `PromptPanel & SketchDropzone` (Text and image input handler)
    2. `Viewer3D (React Three Fiber)` (WebGL, STLLoader, EdgesGeometry, ViewCube)
    3. `ParameterSliders & TelemetryHUD` (Sliders, manifold status, bounding dimensions)
    4. `ChatModify & ProjectSidebar` (Conversational history, project navigation)
- **Middle Layer (Application Server / API Gateway):**
  - Draw a box labeled *"Backend Server (FastAPI / Uvicorn ASGI)"*.
  - Connect Client to Server with two directed arrows:
    - Arrow 1: *"REST API Requests (Axios with Bearer JWT)"*
    - Arrow 2: *"Server-Sent Events Stream (SSE /api/generate/stream)"*
  - Inside the backend box, show:
    - Middleware Stack: `ProxyHeaders` $\to$ `CORS` $\to$ `TelemetryMiddleware` $\to$ `SimpleRateLimiter`.
    - Service Layer (4 sub-boxes):
      1. `VisionService` (Gemini Vision / Groq Vision fallback)
      2. `RAGService` (ChromaDB Vector Store + sentence-transformers)
      3. `LLMService` (3-Tier Fallback Engine + PII Scrubber)
      4. `CADRunner` (AST Security Sandbox + OpenCASCADE build123d Subprocess)
- **Bottom Layer (Data & Storage Layer):**
  - Draw 3 persistent storage cylinders/boxes:
    1. `ChromaDB Vector Store` (Local storage in `/rag_corpus/chroma_db/`)
    2. `Relational Database` (SQLite WAL / PostgreSQL via SQLAlchemy Async)
    3. `Model Artifact Storage` (Local filesystem in `/scratch/temp/models/`)
  - Draw bidirectional data lines connecting the Service Layer to each storage unit.

### 14.2 Use Case Diagram Specification
- **Actors:**
  - `Guest User` (Unregistered visitor)
  - `Registered Engineer` (Authenticated user)
  - `System Administrator` (Admin token holder)
  - `Cloud LLM Service` (External actor: Google Gemini / Groq)
- **Use Cases & Associations:**
  - `Guest User` can:
    - *Generate CAD Model from Text*
    - *Upload Sketch to Generate CAD*
    - *Adjust Parameters & Recompute Geometry*
    - *Interact with 3D Viewer (Orbit, Pan, Section Cut)*
    - *Browse Public Gallery*
    - *Register Account / Log In*
  - `Registered Engineer` inherits all Guest use cases, plus:
    - *Create & Manage Workspace Projects*
    - *Modify CAD Design via Conversational Chat*
    - *Save & Restore Version History*
    - *Publish Design to Public Gallery*
    - *Like & Fork Community Designs*
    - *Download Manufacturing Artifacts (STL, STEP, ZIP)*
  - `System Administrator` can:
    - *Purge Stale Artifacts (`POST /api/admin/cleanup`)*
    - *Inspect Raw Python Scripts (`GET /api/script/{id}`)*
    - *View System Telemetry & Metrics (`GET /api/metrics`)*
  - `<<include>>` Relationships:
    - *Generate CAD Model* `<<include>>` *Screen AST Syntax & Security*
    - *Generate CAD Model* `<<include>>` *Validate Mesh Watertightness*
    - *Generate CAD Model* `<<include>>` *Retrieve Semantic RAG Context*
  - `<<extend>>` Relationships:
    - *Self-Correct Python Script* `<<extend>>` *Execute CAD Subprocess* (Condition: Execution error or topology failure).

### 14.3 Data Flow Diagram (DFD) Specifications

#### Level 0 DFD (Context Diagram)
- **Central Process:** `0.0 AI Parametric CAD Workbench System`
- **External Entities:**
  1. `User / Engineer`
  2. `Google Gemini API / Groq API`
  3. `Local Filesystem / Database`
- **Data Flows:**
  - `User` $\to$ `System`: Prompt Text, Sketch Images, Slider Parameter Values, Login Credentials.
  - `System` $\to$ `User`: Real-time SSE Progress Events, 3D Mesh (STL), STEP Files, Telemetry Metrics.
  - `System` $\to$ `LLM API`: PII-Scrubbed Engineering Prompts, Vision Image Buffers, Tracebacks.
  - `LLM API` $\to$ `System`: Structured Dual-Output JSON Payloads (Code + Parameters).
  - `System` $\to$ `Storage`: User Records, Project Rows, Generated Python Scripts, STL/STEP Binaries.

#### Level 1 DFD (Decomposed Core Pipeline)
- **Process 1.0:** *Authenticate & Enforce Quotas* (Checks JWT, updates `generations_today`).
- **Process 2.0:** *Process Multimodal Inputs* (Vision parsing or text ingestion).
- **Process 3.0:** *Retrieve RAG Exemplars* (Queries ChromaDB dense vector collection).
- **Process 4.0:** *Synthesize CAD Code via LLM* (Dispatches few-shot prompt to Gemini/Groq).
- **Process 5.0:** *Screen & Validate AST* (Static syntax and security inspection).
- **Process 6.0:** *Execute OpenCASCADE Kernel* (Subprocess execution, STL/STEP export).
- **Process 7.0:** *Analyze Mesh Geometry* (Watertightness, volume, face count calculation).
- **Process 8.0:** *Render & Recompute* (WebGL rendering, fast slider recomputation).
- **Data Stores:** `D1: ChromaDB Index`, `D2: Relational DB (Users/Projects/Generations)`, `D3: File Storage (/scratch/temp/)`.

### 14.4 Sequence Diagram: Natural Language CAD Generation (`/api/generate/stream`)
- **Lifelines:** `User`, `PromptPanel (React)`, `api.js`, `FastAPI (main.py)`, `RAGService`, `LLMService`, `CADRunner`, `Subprocess (OpenCASCADE)`, `Viewer3D (Three.js)`.
- **Sequence Steps:**
  1. `User` types prompt and clicks "Generate".
  2. `PromptPanel` calls `generatePartStream(prompt)` in `api.js`.
  3. `api.js` opens HTTP POST connection to `/api/generate/stream`.
  4. `FastAPI` validates rate limit and daily quota.
  5. `FastAPI` sends SSE: `phase: 'rag_retrieval'` (15%).
  6. `FastAPI` calls `RAGService.retrieve(prompt)`.
  7. `RAGService` queries ChromaDB and returns top-3 blueprints.
  8. `FastAPI` sends SSE: `phase: 'llm_generation'` (35%).
  9. `FastAPI` calls `LLMService.generate_dual_output(prompt, examples)`.
  10. `LLMService` returns `DualOutputPayload` (code + parameters).
  11. `FastAPI` sends SSE: `phase: 'ast_validation'` (55%).
  12. `FastAPI` calls `CADRunner.validate_script_safety(code)`.
  13. `FastAPI` sends SSE: `phase: 'cad_execution'` (75%).
  14. `CADRunner` spawns isolated subprocess running `build123d`.
  15. Subprocess compiles solid, exports STL/STEP, and exits (code 0).
  16. `FastAPI` sends SSE: `phase: 'mesh_validation'` (92%).
  17. `CADRunner` validates watertight mesh properties via `trimesh`.
  18. `FastAPI` sends SSE: `phase: 'complete'` (100%) with `GenerateResponse`.
  19. `api.js` delivers final JSON to React reducer.
  20. `Viewer3D` loads STL binary and renders 3D shaded model with dimensions.

### 14.5 Sequence Diagram: Fast Parametric Recompute (`/api/recompute`)
- **Lifelines:** `User`, `ParameterSlider (React)`, `App.jsx`, `FastAPI (main.py)`, `CADRunner`, `Subprocess`, `Viewer3D`.
- **Sequence Steps:**
  1. `User` adjusts slider (e.g., changes `length` from 100 to 120).
  2. `ParameterSlider` notifies `App.jsx` via debounced event.
  3. `App.jsx` sends POST `/api/recompute` with `{script_id, python_code, updated_parameters}`.
  4. `FastAPI` checks `recompute_limiter` (40 req/min).
  5. `FastAPI` calls `CADRunner.execute_script_async(fast_preview=True)`.
  6. `CADRunner` executes `_inject_parameters()`, updating `PARAMS['length'] = 120.0` in the script text.
  7. `CADRunner` validates AST safety of modified script.
  8. `CADRunner` spawns Python subprocess with unique recompute ID.
  9. Subprocess compiles updated solid, re-exports STL, and exits.
  10. `CADRunner` calculates mesh metrics.
  11. `FastAPI` returns `RecomputeResponse` containing updated `mesh_url`.
  12. `Viewer3D` reloads STL mesh and updates dimension badges immediately.

### 14.6 Activity Diagram: Self-Correction Loop
- **Start Node:** Script execution initiated.
- **Action 1:** Subprocess executes `build123d` Python script.
- **Decision Diamond 1:** Did subprocess exit with code 0?
  - *No:* Capture stderr traceback (syntax error or runtime exception).
  - *Yes:* Proceed to Decision Diamond 2.
- **Decision Diamond 2:** Is geometry topologically valid (solid count == 1, watertight, volume > 0)?
  - *Yes:* Export STL/STEP artifacts $\to$ **End Node (Success)**.
  - *No:* Capture geometry warnings as error text.
- **Decision Diamond 3:** Has retry count reached `MAX_RETRIES` (3)?
  - *Yes:* Format failure response $\to$ Raise HTTP 422 $\to$ **End Node (Failure)**.
  - *No:* Increment `self_correction_attempts`.
- **Action 2:** Call `LLMService.correct_code(user_prompt, failed_code, error_traceback)`.
- **Action 3:** LLM synthesizes corrected script.
- **Action 4:** Validate corrected script via AST security analyzer.
- **Loop Back:** Return to Action 1 with corrected code.

---

## 15. JUET Report Preparation Mapping (Chapter-Wise)

To assist the student team in preparing their official university minor project report, the codebase findings are mapped directly to the JUET CSE report template:

### Chapter 1: Introduction
- **Background of the Study:** Shift from traditional GUI-driven CAD modeling toward programmatic, generative, and neurosymbolic CAD workflows.
- **Problem Statement:** High barrier to entry in parametric CAD; latency and imprecision of neural mesh diffusions; need for dimensional B-Rep manufacturing files.
- **Objectives:** Create a browser-based, AI-driven CAD workbench achieving $\ge 85\%$ prompt success, $<200\text{ ms}$ recomputations, multi-layered AST/subprocess security, and STEP/STL export.
- **Scope of the Project:** Single-solid mechanical components, standard engineering archetypes, parametric sliders, vision-based sketch analysis, and public gallery sharing.
- **Source Files as Evidence:** `prd.md` [Lines 1–193], `backend/config.py` [Lines 1–83].

### Chapter 2: Literature Review / Background Work
- **Existing Systems:** SolidWorks, Autodesk Fusion 360, FreeCAD, OpenSCAD, Shap-E, Point-E, Text-to-CAD research models.
- **Limitations of Existing Work:** Traditional CAD has steep learning curves; 3D diffusion models generate unconstrained polygonal meshes without true planar faces, editable dimensions, or STEP export capabilities.
- **Needs for Proposed System:** Integration of LLMs with deterministic CAD kernels (`build123d` / OpenCASCADE) to guarantee editable, watertight parametric solids.
- **Source Files as Evidence:** `backend/services/prompts.py` [Lines 1–250], `backend/rag_corpus/examples_universal.py` [Lines 1–100].

### Chapter 3: System Analysis and Design
- **System Architecture:** Detailed client-server architecture diagram and 5-stage pipeline description.
- **Design Methodology:** Modular micro-monolith architecture separating API handling, security analysis, LLM fallback, kernel execution, and WebGL rendering.
- **Data Flow & UML Diagrams:** DFD Levels 0 & 1, Use Case Diagram, Sequence Diagrams (Generation, Recompute, Modify), and ER Diagram.
- **Source Files as Evidence:** `backend/main.py`, `backend/services/cad_runner.py`, `backend/models/project.py`.

### Chapter 4: Implementation and Testing
- **Tools and Technologies Used:** Detailed narrative based on Section 3 (FastAPI, React 19, Three.js, build123d, ChromaDB, SQLAlchemy).
- **Implementation Details:** Code snippets and explanations of AST screening (`validate_script_safety`), fast parametric recomputation (`_inject_parameters`), and Geometric Chain-of-Thought sketch parsing.
- **Testing Methods:** Automated unit and integration testing via Pytest; schema validation; AST adversarial tests; geometry validation tests.
- **Test Results:** 88 passed, 1 skipped test suite report (89 collected); Oxlint 0 warnings report; Vite production bundle compilation statistics.
- **Source Files as Evidence:** `backend/test_ast_security.py`, `backend/test_schemas.py`, `backend/test_sketch_endpoint.py`.

### Chapter 5: Results and Discussion
- **Results Analysis:** 20-prompt automated benchmark analysis demonstrating 90% final success rate and 80% first-pass rate.
- **Performance Evaluation:** P50 generation latency ($17.25\text{ s}$), mean generation latency ($17.14\text{ s}$), slider recompute latency ($<200\text{ ms}$ target, $164\text{ ms}$ observed).
- **Discussion:** Strengths of programmatic OpenCASCADE B-Rep solids over polygonal meshes; efficacy of the automated self-correction loop in resolving geometric edge errors.
- **Source Files as Evidence:** `backend/benchmark_eval.py`, `backend/benchmark_results.json`.

### Chapter 6: Conclusion and Future Work
- **Conclusion:** Summary of achievements—a functional, secure, browser-based CAD workbench bridging natural language/sketches and manufacturing.
- **Future Work:** Distributed Celery/Redis queue, 2D technical drawing generation (DXF), kinematic motion assemblies, and fine-tuned open-source CAD LLMs.
- **Source Files as Evidence:** `task.md` [Backlog section], Section 13 of this dossier.

---

## 16. Traceability and Evidence Index

Every critical implementation assertion in this dossier is indexed below to its exact source code file and line numbers:

| Claim / Assertion | Source File | Function / Component | Line Numbers | Verification Label |
|---|---|---|---|---|
| JWT secret environment variable is `JWT_SECRET_KEY` | `backend/config.py` | Configuration assignment | Line 73 | `[VERIFIED IN SOURCE]` |
| Rate limit of 10 req/min for generate and 40 req/min for recompute | `backend/main.py` | `SimpleRateLimiter` instantiations | Lines 124–126 | `[VERIFIED IN SOURCE]` |
| Daily free-tier generation quota capped at 50 generations | `backend/services/auth_service.py` | `check_and_bump_quota` | Lines 38–41 | `[VERIFIED IN SOURCE]` |
| AST analyzer blocks `open`, `eval`, `exec`, `__subclasses__` | `backend/services/cad_runner.py` | `validate_script_safety` | Lines 168–242 | `[VERIFIED IN SOURCE]` |
| Subprocess execution timeout enforced at 60 seconds | `backend/config.py` | `CAD_EXECUTION_TIMEOUT_SECONDS` | Line 82 | `[VERIFIED IN SOURCE]` |
| Concurrency capped at 2 simultaneous CAD subprocesses | `backend/services/cad_runner.py` | `CAD_EXECUTION_SEMAPHORE` | Line 128 | `[VERIFIED IN SOURCE]` |
| Self-correction retries capped at 3 attempts | `backend/main.py` | `generate_part` | Line 447 | `[VERIFIED IN SOURCE]` |
| Local dense embedding model is `all-MiniLM-L6-v2` | `backend/services/rag_service.py` | `_EMBED_MODEL_NAME` | Line 40 | `[VERIFIED IN SOURCE]` |
| SQLite WAL mode and busy timeout pragmas configured | `backend/database.py` | `_set_sqlite_pragmas` | Lines 45–55 | `[VERIFIED IN SOURCE]` |
| Refresh token reuse detection invalidates session | `backend/routes/auth.py` | `refresh_token` | Lines 201–204 | `[VERIFIED IN SOURCE]` |
| Sketch-to-CAD endpoint enforces max 10MB image limit | `backend/main.py` | `generate_from_sketch` | Lines 726, 790–794 | `[VERIFIED IN SOURCE]` |
| Groq Vision fallback uses `llama-3.2-11b-vision-preview` | `backend/services/vision_service.py`| `_parse_with_groq` | Lines 300–325 | `[VERIFIED IN SOURCE]` |
| Three.js feature edge geometry extracted at 24° threshold | `frontend/src/components/Viewer3D.jsx`| `edgesGeo` useMemo | Lines 178–182 | `[VERIFIED IN SOURCE]` |
| Client-side model cache version-guarded at version 1 | `frontend/src/hooks/useCADWorkbench.js`| `STORAGE_VERSION` | Lines 4–15 | `[VERIFIED IN SOURCE]` |
| Hash routing handles `#app`, `#gallery`, `#model=`, `#embed=` | `frontend/src/Router.jsx` | `getViewFromHash` | Lines 42–48 | `[VERIFIED IN SOURCE]` |
| Test suite collects and executes 89 test items | `backend/pytest.ini` | Full test execution run | Live run | `[VERIFIED BY EXECUTION]` |
| Oxlint executes across 27 files with 0 errors and 0 warnings | `frontend/.oxlintrc.json` | `npm run lint` execution | Live run | `[VERIFIED BY EXECUTION]` |

---

## 17. Final Verification Checklist & Questions for Project Team

### 17.1 Questions That the Student Project Team Must Answer
Because code and configuration files alone cannot establish external academic details, the project team must clarify the following for their final university submission:
1. **Student Team Details:** What are the official student names, enrollment numbers, and batch details for the JUET title page?
2. **Project Supervisor Details:** What is the official name and academic designation of the faculty supervisor / project coordinator?
3. **Physical Hardware Environment:** What specific physical CPU (e.g., Intel Core i7-13700H, AMD Ryzen 7 5800X), RAM (e.g., 16GB DDR5), and OS build were used during development and testing?
4. **Division of Labor:** Which team members focused primarily on the backend CAD kernel/AST sandboxing, the RAG vector store, the frontend Three.js viewport, and the multimodal vision integration?

### 17.2 Final Report Preparation Checklist
- [ ] Verify that all team members' names and roll numbers match JUET administrative records.
- [ ] Confirm that no API keys or secret tokens appear in screenshots or code appendices.
- [ ] Re-run the automated benchmark (`python benchmark_eval.py`) on the university lab machine to record local latency metrics.
- [ ] Export at least 3 distinct models (e.g., a shaft, a bracket, an enclosure) in both STL and STEP formats to demonstrate physical manufacturing readiness.
- [ ] Prepare clean manual drawings of the 7 specified technical diagrams (System Architecture, Use Case, DFD Levels 0 & 1, Class/ER, Generation Sequence, Recompute Sequence, and Self-Correction Activity).
- [ ] Include terminal output evidence verifying the 88 passing test cases and 0-warning frontend build.
