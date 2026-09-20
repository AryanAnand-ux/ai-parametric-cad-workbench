# Task Board
## AI Parametric CAD Workbench

**Last Updated:** September 20, 2026  
**Sprint:** Active Development  

> This file tracks current, upcoming, and completed development tasks.
> Update this file as work progresses. Mark items [x] when done.

---

## In Progress

- [ ] Documentation suite — prd.md, architecture.md, rules.md, design.md, task.md, memory.md (in progress)

---

## Backlog — High Priority

### Backend
- [ ] Migrate SQLite → PostgreSQL for production deployments
- [ ] Add Alembic migrations (replace `create_all` on startup)
- [ ] Add streaming SSE progress for generation pipeline stages (RAG → LLM → Build → Export)
- [ ] Implement model thumbnail generation (render 3D screenshot server-side)
- [ ] Add rate limit headers to API responses (`X-RateLimit-Remaining`, `Retry-After`)
- [ ] `test_universal_archetypes.py` — run all 20 archetype prompts against live LLM in CI-optional mode

### Frontend
- [ ] Gallery page: add search/filter by discipline, material, complexity
- [ ] Parameter sidebar: add parameter grouping by category (dimensions, features, tolerances)
- [ ] Add keyboard shortcuts (G = Generate, R = Recompute, E = Export, ? = Tour)
- [ ] Onboarding tour: persist completion state in `localStorage` so it doesn't re-show
- [ ] Mobile responsive pass for workbench (sidebar collapse, toolbar reflow)

### DevOps
- [ ] Add GitHub Actions workflow for pytest on every PR (not just weekly benchmark)
- [ ] Add Dockerfile healthcheck for the backend container
- [ ] Set up Dependabot for Python + npm dependency updates

---

## Backlog — Medium Priority

- [ ] Dark mode toggle (CSS custom property swap)
- [ ] Code inspector: syntax highlighting for generated Python (Prism.js or similar)
- [ ] Export: add batch export (download all formats as ZIP)
- [ ] Gallery: add pagination / infinite scroll
- [ ] Projects sidebar: drag-to-reorder projects
- [ ] Add `CHANGELOG.md` to track version history

---

## Backlog — Low Priority / Ideas

- [ ] AI-suggested next prompts (LLM suggests variations based on current model)
- [ ] Split-view: prompt history timeline on the left
- [ ] 3D viewer: measurement tool (distance between two points)
- [ ] 3D viewer: section cut plane tool
- [ ] Add build123d tutorial/docs link in onboarding tour
- [ ] Telemetry HUD: add polygon count, material info

---

## Completed

- [x] Week 1-2: Project scaffolding, FastAPI setup, basic NL → CAD pipeline
- [x] Week 3: LLM service multi-tier fallback (Gemini → Groq), self-correction loop
- [x] Week 4: build123d CAD engine integration, CAD runner subprocess sandbox
- [x] Week 4: RAG corpus setup (ChromaDB + sentence-transformers)
- [x] Week 5: AST security validation, rate limiting, temp file cleanup
- [x] Week 6: SQLAlchemy database, user auth (JWT + bcrypt), projects CRUD
- [x] Week 7: React frontend — Viewer3D (React Three Fiber), workbench layout
- [x] Week 7: Parameter sliders, recompute endpoint, parameter editing
- [x] Week 8: Chat-to-modify panel, modification history
- [x] Week 8: Gallery page, share modal, public gallery backend
- [x] Week 8: Onboarding tour, auth modal (login/register)
- [x] Week 9+: Universal archetypes — 20 CAD archetypes, 121-doc RAG index
- [x] Navbar refactor — compact segmented controls, user dropdown, unified status indicator
- [x] Logo → home navigation — brand logo routes to landing page via `onGoHome` callback
- [x] CI/CD — 33/33 pytest tests passing, Vite production build verified
- [x] Documentation suite — all 6 core .md files created (this task)

---

## Notes

- Backend test suite: `cd backend && python -m pytest -v` (33 tests, ~45s)
- Frontend dev server: `cd frontend && npm run dev` (Vite, port 5173)
- Backend dev server: `cd backend && uvicorn main:app --reload --port 8000`
- RAG index rebuild: `python -c "from services.rag_service import RAGService; RAGService.build_index()"`
