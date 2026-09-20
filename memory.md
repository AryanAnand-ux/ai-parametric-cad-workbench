# Project Memory
## AI Parametric CAD Workbench

**Last Updated:** September 20, 2026  

> This file is the living memory of the project — key decisions, lessons learned, known issues, environment context, and session notes. Update it after any significant decision or debugging session.

---

## 1. Project Context

- **Project name:** AI Parametric CAD Workbench (Minor Project)
- **Repository:** `AryanAnand-ux/ai-parametric-cad-workbench`
- **Local path:** `D:\Projects\Minor_project`
- **Stack:** FastAPI backend + Vite/React frontend
- **Dev ports:** Backend `:8000`, Frontend `:5173`
- **Database:** SQLite (`backend/cad_workbench.db`)
- **Python:** 3.11, venv at `backend/venv/`
- **Node:** via `npm` in `frontend/`

---

## 2. Key Architecture Decisions

### 2.1 Hash-Based Routing (No React Router)
**Decision:** Use `window.location.hash` for routing (`#app`, `#gallery`, `''`)  
**Reason:** Avoids server-side routing config; simple SPA with only 3 views  
**Files:** `frontend/src/Router.jsx`  
**Note:** Always use `window.location.hash = ''` for home, never `window.location.href`

### 2.2 useReducer for Workbench State
**Decision:** All workbench state in `useCADWorkbench` hook via `useReducer`  
**Reason:** Prevents prop-drilling across 13+ components; enables undo history  
**Files:** `frontend/src/hooks/useCADWorkbench.js`  
**Note:** Do not add parallel `useState` for model data — always dispatch to the reducer

### 2.3 Local ChromaDB (No Cloud Vector DB)
**Decision:** ChromaDB persistent store at `backend/rag_corpus/chroma_db/`  
**Reason:** Zero API cost, offline-capable, sufficient for 121-doc corpus  
**Note:** Index is built once and persisted; rebuild only if corpus changes

### 2.4 Multi-Tier LLM Fallback
**Decision:** Gemini Tier 1 → Tier 2 → Groq Tier 3  
**Reason:** Gemini has best CAD JSON output quality; Groq is fast and free fallback  
**Files:** `backend/services/llm_service.py`  
**Note:** Self-correction loop capped at 3 to prevent quota exhaustion

### 2.5 AST Security Sandboxing
**Decision:** Validate all LLM-generated Python with `ast.parse` before subprocess execution  
**Reason:** LLMs can be prompted to inject malicious code; AST check is the last gate  
**Files:** `backend/services/cad_runner.py`, `backend/test_ast_security.py`  
**Note:** This check is MANDATORY — never bypass it even in dev mode

### 2.6 Temp Files Outside Backend Source Tree
**Decision:** Temp/model files go to `scratch/temp/` (project root level)  
**Reason:** Uvicorn's WatchFiles reloader was detecting generated `.py` and `.stl` files and restarting the server mid-request, causing 500 errors  
**Config:** `TEMP_DIR = BASE_DIR.parent / "scratch" / "temp"` in `config.py`

### 2.7 Vanilla CSS Only
**Decision:** No TailwindCSS — pure CSS in `frontend/src/index.css`  
**Reason:** Full control over design tokens; no purge config complexity; smaller bundle  
**Files:** `frontend/src/index.css` (~44KB — intentionally large, all styles centralized)

---

## 3. Known Issues & Gotchas

### 3.1 build123d Import Time
- First import of `build123d` in a new subprocess takes 3–5 seconds (OCCT loading)
- Subsequent subprocesses reuse the system library cache — faster
- **Workaround:** Warm-up subprocess on startup (future enhancement)

### 3.2 ChromaDB Warning: Telemetry
- ChromaDB logs a telemetry opt-in warning on first run
- Safe to ignore; it does not affect functionality
- To suppress: set `ANONYMIZED_TELEMETRY=false` in environment

### 3.3 WatchFiles Reloader (RESOLVED)
- **Issue:** `uvicorn --reload` was restarting mid-request when CAD scripts were written to `backend/temp/`
- **Fix:** Moved temp dir to `scratch/temp/` (outside backend source tree)
- **Status:** Resolved — do not move temp files back inside `backend/`

### 3.4 Gemini Web Client (Optional Feature)
- `services/gemini_web_client.py` is a reverse-engineered Gemini web API client
- Requires valid browser cookies (`GEMINI_WEB_COOKIE`) and is NOT officially supported
- Enable only with `GEMINI_WEB_ENABLED=true` in `.env`
- May break with Gemini web UI updates

### 3.5 SQLite Concurrency
- SQLite with `aiosqlite` supports limited concurrent writes
- Under load (multiple users generating simultaneously), writes may queue
- **Long-term fix:** Migrate to PostgreSQL (see task.md backlog)

### 3.6 RAG Index Cold Start
- If `RAG_BUILD_ON_STARTUP=true`, backend takes 30–60s to start (downloads embedding model)
- Default is `false` — index must be pre-built with `RAGService.build_index()`
- Model is cached at `~/.cache/huggingface/` after first download

---

## 4. Environment Setup (Quick Reference)

```bash
# Backend setup (first time)
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Build RAG index (run once)
python -c "from services.rag_service import RAGService; RAGService.build_index()"

# Start backend
uvicorn main:app --reload --port 8000

# Frontend setup (first time)
cd frontend
npm install

# Start frontend
npm run dev   # http://localhost:5173
```

### Environment Variables (`.env`)
```
GEMINI_API_KEY=<your-key>
GROQ_API_KEY=<your-key>
SECRET_KEY=<random-64-char-string>
ADMIN_TOKEN=<random-string>
ALLOWED_ORIGINS=http://localhost:5173
ENVIRONMENT=development
```

---

## 5. Session Notes / Change Log

### September 20, 2026
- Created documentation suite: prd.md, architecture.md, rules.md, design.md, task.md, memory.md
- Deleted WEEKLY_PLAN.md (content absorbed into task.md and memory.md)
- Deleted frontend/README.md (redundant with new architecture.md)
- Deleted docs/review/ folder (11 weekly reports — historical content preserved in git history)
- Added mandatory live-update rule to rules.md §6.2: every code/design change must update the relevant doc file in the same commit

### September 19, 2026
- Refactored workbench navbar: compact segmented controls, user dropdown, unified status indicator
- Fixed logo → home navigation: brand logo now correctly calls `onGoHome` (routes back to landing via hash reset)
- Verified: 33/33 pytest tests passing, Vite production build successful
- Pushed all changes to `main` branch

### September 18, 2026
- Implemented 20 universal CAD archetypes for RAG corpus (121 documents total)
- Ran benchmark: ChromaDB index built successfully
- Verified frontend landing page (all sections rendered correctly)
- Ran full test suite: 33/33 passed

### Earlier Sessions
- Weeks 1–9: See `docs/review/week1.md` through `docs/review/week9_onwards.md` for detailed weekly progress reports

---

## 6. Testing Reference

```bash
# Run all tests
cd backend && python -m pytest -v

# Run specific test file
python -m pytest test_universal_archetypes.py -v

# Run with coverage (if pytest-cov installed)
python -m pytest --cov=. --cov-report=html

# Run benchmark suite only
python -m pytest test_schemas.py test_ast_security.py test_llm_parser.py \
  test_geometry_validation.py test_recompute_validation.py -v
```

### Current Test Suite (33 tests, all passing)
| File | Tests | Description |
|------|-------|-------------|
| `test_schemas.py` | 8 | Pydantic schema validation |
| `test_ast_security.py` | 5 | AST sandbox patterns |
| `test_llm_parser.py` | 4 | LLM JSON response parsing |
| `test_geometry_validation.py` | 4 | Mesh geometry checks |
| `test_recompute_validation.py` | 3 | Recompute parameter contracts |
| `test_universal_archetypes.py` | 5 | 20 archetype definitions |
| `test_auth_projects.py` | 4 | Auth + project CRUD |

---

## 7. Useful Commands

```bash
# Check backend is running
curl http://localhost:8000/api/health

# Check RAG index status
python -c "from services.rag_service import RAGService; print(RAGService.get_stats())"

# Generate a model via API (test)
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A simple cube 50mm x 50mm x 50mm"}'

# Rebuild frontend for production
cd frontend && npm run build

# Docker full stack
docker-compose up --build
```
