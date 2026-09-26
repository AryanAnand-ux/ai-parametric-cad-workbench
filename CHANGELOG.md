# Changelog
## AI Parametric CAD Workbench

All notable changes to this project are documented in this file.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Fixed
- **CI dependency gap** — Added `sqlalchemy[asyncio]` + explicit `greenlet` + `bcrypt` to `backend/requirements.txt` (fixed 8 consecutive CI collection failures); removed unused `sse-starlette`

### Planned
- PostgreSQL migration (replace SQLite for production)
- Alembic database migrations
- Model thumbnail server-side rendering
- Dark mode toggle

---

## [0.9.0] — 2026-09-25

### Added
- **Gallery Publish Flow** — Publish button in workbench toolbar lets logged-in users push any generated model to the public community gallery
- **Gallery nav button** — Header toolbar now has a direct Gallery shortcut alongside Publish
- **`generation_id` in API response** — Both `/api/generate` and `/api/generate/stream` now return the database `generation_id` so the frontend can reference it for publish/fork flows
- **Community gallery seeded** — 5 real geometry-compiled public models added via `backend/seed_gallery.py`:
  - Involute Spur Gear with Lightening Holes
  - Heavy-Duty Gusseted L-Bracket
  - Parametric Electronics Enclosure Box
  - Ergonomic Desktop Phone & Tablet Stand
  - Precision Stepped Drive Shaft

### Changed
- **`publish_design` endpoint** — Now accepts flexible JSON body (list `["tag"]` or dict `{"tags": ["tag"]}`)
- **`useCADWorkbench.js`** — Added `generationId` to state, `APPLY_PART_RESPONSE` action, and localStorage persistence

### Removed
- **Atelier Memberships pricing section** — Three-tier pricing cards removed from landing page (FAQ accordion now follows Testimonials directly)

### Fixed
- **`RAGService.get_stats()`** — Added missing method that was causing `AttributeError` in test suite

---

## [0.8.0] — 2026-09-20

### Added
- **Keyboard shortcuts** — `G` (Generate), `R` (Force Recompute), `E` (Export), `?` (Tour), `Z` (Undo) registered globally in workbench
- **Rate limit headers** — `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` on API responses; HTTP 429 with `Retry-After`
- **Gallery live search & discipline chips** — Debounced client-side search + extended tags filter (bracket, enclosure, heatsink, gear, shaft, pulley, flange, manifold, aerospace, robotics, thermal, fixture)
- **Full-Stack CI/CD** — GitHub Actions workflow runs pytest + Vite production build on every push and PR
- **Onboarding tour persistence** — localStorage caches completion flag; reset via user account dropdown

### Changed
- **Workbench navbar refactor** — Compact segmented viewport controls, user dropdown, unified status indicator
- **Logo navigation** — Brand logo click routes to landing page via `onGoHome` callback

### Fixed
- **TDZ error in App.jsx** — Temporal dead zone crash on `generationId` access fixed

---

## [0.7.0] — 2026-09-14

### Added
- **Universal CAD Archetypes** — 20 archetype CAD part definitions in `rag_corpus/examples_universal.py`
- **121-document RAG index** — ChromaDB vector store rebuilt with full archetype coverage
- **`test_universal_archetypes.py`** — Validates all 20 archetype prompt→code definitions
- **Archetype preset buttons** in frontend prompt panel for quick selection

### Changed
- ChromaDB collection rebuilt to include all universal examples
- Torus handle fixed for coffee mug archetype; gear and consumer directives refined

---

## [0.6.0] — 2026-09-07

### Added
- **Public Gallery page** — Browse, search, like, and fork community CAD designs
- **Share modal** — Share current model to gallery with one click
- **Auth modal** — Login / register with JWT-based auth; guest mode supported
- **Onboarding tour** — Step-by-step first-time user guide with localStorage persistence
- **Projects sidebar** — Save, load, and version-control designs per user account
- **Chat-to-Modify panel** — Natural language modifications tracked in conversation history

### Changed
- Projects API returns version history per project with mesh delta info

---

## [0.5.0] — 2026-08-31

### Added
- **AST security sandbox** — All LLM-generated Python validated via `ast.parse` before execution; blocks `subprocess`, `exec`, `eval`, `open`, `socket`, `requests`
- **Rate limiting** — Sliding-window per-IP limiter (10 req/min generate, 40 req/min recompute)
- **Artifact cleanup** — `ArtifactCleanupManager` removes temp files after configurable TTL
- **Script ID allowlist** — `is_safe_script_id()` validates recompute targets

---

## [0.4.0] — 2026-08-24

### Added
- **React Three Fiber 3D viewer** — Interactive mesh render with orbit, zoom, pan
- **Parameter sliders** — Named parameters exposed from generated code; real-time recompute
- **Recompute endpoint** — `POST /api/recompute` re-runs script with updated parameter values in <200ms
- **Multi-format export** — STL, STEP, OBJ, GLB download endpoints

---

## [0.3.0] — 2026-08-17

### Added
- **SQLAlchemy database** — Async SQLite with `User`, `Project`, `Generation`, `Version` models
- **JWT authentication** — Register, login, token refresh via `passlib[bcrypt]`
- **Projects CRUD** — `GET/POST /api/projects`, version history per project

---

## [0.2.0] — 2026-08-10

### Added
- **Multi-tier LLM fallback** — Gemini Tier 1 → Tier 2 → Groq Tier 3; self-correction loop (max 3 retries)
- **RAG corpus** — ChromaDB + sentence-transformers for retrieval-augmented code generation
- **`build123d` integration** — CAD script executed in isolated async subprocess with timeout
- **Dual-output schema** — LLM returns both Python code and parameter list in one structured JSON response

---

## [0.1.0] — 2026-08-03

### Added
- Project scaffolding — FastAPI backend, Vite/React frontend, monorepo layout
- `POST /api/generate` — Basic natural language → CAD pipeline (prompt → LLM → execute → STL)
- `GET /api/health` — Backend health check with LLM provider status
- Basic Pydantic schemas for request/response validation
- Docker setup (`Dockerfile` + `docker-compose.yml`)
