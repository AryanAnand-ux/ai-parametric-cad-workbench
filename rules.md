# Rules & Coding Standards
## AI Parametric CAD Workbench

**Version:** 1.0  
**Last Updated:** September 2026  
**Applies to:** All contributors (human and AI agents)

---

## 1. Purpose

This document defines the mandatory coding conventions, architecture rules, and safety constraints for the project. All code changes — whether from human developers or AI coding assistants — must comply with these rules.

---

## 2. General Principles

1. **Clarity over cleverness** — Write code that a fresh reader can understand in 5 minutes.
2. **Fail loudly, recover gracefully** — Raise informative exceptions; never silently swallow errors.
3. **Security is non-negotiable** — Any code execution path must be sandboxed or validated.
4. **No orphaned files** — Every generated artifact (STL, GLB, STEP, .py scripts) must be cleaned up by the `ArtifactCleanupManager`.
5. **Tests before merge** — All 33 pytest tests must pass before pushing to `main`.

---

## 3. Backend Rules (Python / FastAPI)

### 3.1 Code Style
- **Python version:** 3.11+
- **Formatter:** No strict formatter enforced, but PEP 8 conventions apply
- **Type hints:** Required on all function signatures and return types
- **Docstrings:** Required on all services and public functions (triple-quote, first line summary)
- **Logging:** Use `logger = logging.getLogger("cad_workbench.<module>")` — never `print()`

### 3.2 FastAPI Conventions
- All endpoints must have explicit Pydantic request/response schemas defined in `schemas.py`
- Router files go in `backend/routes/` — never define routes directly in `main.py` (exception: core pipeline endpoints `/api/generate`, `/api/recompute`, `/api/modify`)
- Use `Depends()` for auth injection — never read headers manually in route handlers
- Return `HTTPException` with informative `detail` strings, not raw `500` responses

### 3.3 LLM / AI Rules
- **Never call LLM APIs synchronously in the request thread** — use `asyncio.to_thread` or background tasks for long operations
- The **multi-tier fallback order** must be preserved: Gemini Tier 1 → Tier 2 → Groq Tier 3
- The **self-correction loop** cap is 3 retries — do not increase this without load testing
- **Never send user data to the LLM without sanitization** — strip PII patterns before injection into prompts
- RAG retrieval: always retrieve **top-3** examples (k=3) — changing this affects generation quality

### 3.4 CAD Execution Security Rules
- **ALL LLM-generated Python must pass AST validation before execution** — this rule is absolute and non-negotiable
- Blocked AST node types / names: `subprocess`, `os.system`, `os.popen`, `exec`, `eval`, `compile`, `__import__`, `open`, `socket`, `requests`
- Use `is_safe_script_id()` before any recompute operation — never trust user-supplied script IDs directly
- CAD scripts are executed in an **isolated subprocess** with a timeout — never `exec()` them in-process
- Temp files go in `scratch/temp/` (OUTSIDE the backend source tree) to prevent `WatchFiles` reloader from triggering on generated files

### 3.5 Database Rules
- Use **async SQLAlchemy sessions** (`AsyncSession`) — no sync DB calls in async route handlers
- Always use `await db.commit()` after writes; use `await db.rollback()` in `except` blocks
- Migrations: SQLAlchemy `create_all` is used for simplicity (dev); for production, use Alembic
- Never store plaintext passwords — always `passlib[bcrypt]` hashing

### 3.6 Rate Limiting
- Rate limiters are defined in `main.py` as module-level singletons — do not instantiate per-request
- `SimpleRateLimiter` prunes stale buckets when `len(history) > 256` — this cap must not be removed

### 3.7 Testing Rules
- Test files must be named `test_<feature>.py` at the `backend/` root
- All tests use `pytest` + `pytest-asyncio`
- Mark async tests with `@pytest.mark.asyncio`
- Tests that call live LLM APIs must be skipped in CI with `pytest.mark.skipif(not GEMINI_API_KEY, ...)`
- Minimum test coverage: all schema models, all AST security patterns, LLM response parsing

---

## 4. Frontend Rules (React / JavaScript)

### 4.1 Code Style
- **JavaScript (ES2022+)** — no TypeScript (project uses JSX)
- **Functional components only** — no class components
- **React Hooks** — `useState`, `useReducer`, `useCallback`, `useRef`, `useEffect`
- Props: use destructuring in function signatures
- No inline styles on components — all styles go in `index.css`

### 4.2 State Management Rules
- **All workbench state lives in `useCADWorkbench`** (`useReducer`) — do not create parallel `useState` atoms for model/viewport state
- **Auth state lives in `useAuth`** — do not duplicate auth logic in components
- State persistence: model state is serialized to `localStorage` as `cad_last_model` — keep this schema stable
- Reducer actions: use descriptive `type` strings (`SET_MESH`, `SET_LOADING`, `UNDO_MODEL`, etc.)

### 4.3 Styling Rules
- **No TailwindCSS** — vanilla CSS only, in `src/index.css`
- **No inline `style={{}}` props** on top-level layout elements (viewport, header, sidebar)
- CSS custom properties (`--color-*`, `--space-*`) must be used for all design tokens
- Dark-mode aware: use semantic color variables, not hardcoded hex values in components
- Animation: use CSS `transition` / `@keyframes` — no JS-driven animation libraries

### 4.4 Navigation Rules
- Routing is **hash-based** via `Router.jsx` — do not add React Router or any router library
- `goToHome()` always clears the hash: `window.location.hash = ''`
- Brand logo in workbench header must always call `onGoHome()` — this is user-tested behavior
- Never navigate programmatically with `window.location.href` — always use hash

### 4.5 API Rules
- All API calls go through `src/api.js` — never use raw `fetch` in components
- `API_BASE_URL` is the single source of truth for the backend URL
- Always handle loading + error states after API calls
- Streaming responses (SSE) must use `EventSource` or `ReadableStream` — never `fetch` with large timeouts

### 4.6 3D Viewer Rules
- The 3D viewer lives exclusively in `Viewer3D.jsx` — no Three.js imports in `App.jsx`
- Material, lighting, and camera presets are defined as constants in `ViewportToolbar.jsx`
- `OrbitControls` must be enabled at all times — never lock user camera
- Performance: use `useGLTF` for model loading (caches between recomputes)

---

## 5. Git Rules

- **Branch:** Always work on a feature branch, merge to `main` via PR
- **Commits:** Conventional commit format: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`
- **Never commit to `main` directly** without CI passing
- **`.env` files are never committed** — use `.env.example` as template
- `node_modules/`, `venv/`, `__pycache__/`, `scratch/temp/` are in `.gitignore`

---

## 6. Documentation Rules

- `prd.md` — Product requirements (what & why)
- `architecture.md` — System design (how it's built)
- `rules.md` — This file (coding standards)
- `design.md` — UI/UX design system (colors, typography, components)
- `task.md` — Active development tasks and sprint backlog
- `memory.md` — Project decisions, learnings, and session notes
- `README.md` — Public-facing quickstart (keep concise, link to docs/)
- `docs/review/` — Weekly progress reports (do not modify historical weeks)
- **Delete** any ad-hoc markdown files after their content is incorporated into the above

---

## 7. Security Checklist (Pre-Deploy)

- [ ] All `ADMIN_TOKEN`, `SECRET_KEY`, `GEMINI_API_KEY` values are set from environment (not hardcoded)
- [ ] CORS `ALLOWED_ORIGINS` is restrictive (no wildcard `*` in production)
- [ ] AST validator tests pass (`test_ast_security.py`)
- [ ] Rate limiters are active (`generate_limiter`, `modify_limiter`, `recompute_limiter`)
- [ ] Temp file cleanup is scheduled (`ArtifactCleanupManager`)
- [ ] Database passwords are bcrypt-hashed (`test_auth_projects.py`)
