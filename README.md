# AI Parametric CAD Workbench

> **Generate 3D CAD models from natural language prompts — directly in your browser.**

A full-stack AI-powered engineering tool: describe a part in plain English, get a parametric 3D model back in seconds, then tweak parameters or refine via chat.

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Gemini API key (or Groq API key for fallback)

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env           # Edit with your API keys

# Build RAG index (first time only)
python -c "from services.rag_service import RAGService; RAGService.build_index()"

# Start backend
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev     # http://localhost:5173
```

### Docker (full stack)
```bash
docker-compose up --build
```

---

## Documentation

| File | Purpose |
|------|---------|
| [prd.md](./prd.md) | Product requirements — what & why |
| [architecture.md](./architecture.md) | System design — how it's built |
| [design.md](./design.md) | UI/UX design system |
| [rules.md](./rules.md) | Coding standards & constraints |
| [task.md](./task.md) | Active tasks & backlog |
| [memory.md](./memory.md) | Key decisions, known issues, session notes |
| [docs/review/](./docs/review/) | Weekly progress reports |

---

## Key Features

- **Natural Language → CAD** — Describe a part, get a parametric 3D model
- **Parametric Editing** — Adjust named parameters (width, height, wall_thickness) with sliders
- **Chat-to-Modify** — Refine your model in natural language after generation
- **Multi-Format Export** — STL, STEP, OBJ, GLB
- **Public Gallery** — Browse and share community models
- **User Accounts** — Save projects, track version history

---

## Tech Stack

**Backend:** FastAPI · build123d · ChromaDB · Gemini/Groq · SQLite · JWT Auth  
**Frontend:** React 18 · Vite · React Three Fiber · Vanilla CSS

---

## Tests

```bash
cd backend
python -m pytest -v    # 33 tests, ~45 seconds
```

---

## License

MIT
