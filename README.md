# AI-Driven Parametric CAD Workbench

> **Natural Language → 3D Solid Model.** Type a description, get an interactive parametric 3D part you can tune with sliders and export as STL/STEP.

## 🚀 Project Overview

This system bridges the gap between natural language design intent and production-ready CAD output. A user types something like *"a hollow cylinder with 20mm outer radius and 5mm wall thickness"* and the system:

1. **Generates** executable Python code via a 3-tier LLM pipeline (Gemini 2.0 Flash → Gemini 2.5 Flash → Groq Llama-3.3-70B)
2. **Executes** the script in an isolated subprocess using the trimesh geometry kernel
3. **Exports** an STL mesh + STEP file for download or WebGL preview
4. **Provides** UI parameter sliders for sub-200ms recomputation without re-calling the LLM

---

## 👥 Team

| Role | Responsibility |
|------|---------------|
| **Lead (AI/RAG)** | LLM service, RAG pipeline, self-correction loop |
| **Partner 2 (Backend/Geometry)** | FastAPI, CAD subprocess runner, geometry export |
| **Partner 3 (Frontend/WebGL)** | React + Three.js viewer, parameter slider UI |

---

## 📁 Repository Structure

```
ai-parametric-cad-workbench/
├── .gitignore
├── README.md
├── WEEKLY_PLAN.md
└── backend/
    ├── .env.example          ← Copy to .env and add your API keys
    ├── config.py             ← Centralized paths and API key config
    ├── main.py               ← FastAPI app with all route definitions
    ├── schemas.py            ← Pydantic models: DualOutputPayload, CADParameter, etc.
    ├── requirements.txt      ← All Python dependencies
    ├── run.bat               ← Windows: start the server
    ├── run_tests.bat         ← Windows: run all test suites
    ├── test_pipeline.py      ← Week 1-2: CAD runner & geometry tests
    ├── test_week3_llm.py     ← Week 3: LLM integration & schema tests
    ├── test_api.py           ← Week 3: FastAPI endpoint tests
    └── services/
        ├── __init__.py
        ├── freecad_runner.py ← Async subprocess CAD executor + param injection
        ├── exporter.py       ← Mesh inspection (STL → OBJ conversion)
        ├── cleanup.py        ← Artifact lifecycle manager
        └── llm_service.py    ← 3-tier LLM orchestrator with self-correction
```

> **Note:** `frontend/` directory will be created in **Week 9** (React + Three.js WebGL viewer).

---

## ⚙️ Backend Setup (All Team Members)

### 1. Clone the Repository
```bash
git clone https://github.com/AryanAnand-ux/ai-parametric-cad-workbench.git
cd ai-parametric-cad-workbench/backend
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys ⚠️
```bash
# Copy the example file
copy .env.example .env       # Windows
cp .env.example .env         # Linux/macOS

# Edit .env and add your real keys:
# GEMINI_API_KEY=  → get from https://aistudio.google.com/apikey (free)
# GROQ_API_KEY=    → get from https://console.groq.com/keys (free)
```
> **NEVER commit your `.env` file. It is in `.gitignore`.**

### 5. Start the Server
```bash
# Windows (double-click or from terminal):
run.bat

# Or manually:
python main.py
```

Server starts at: **http://localhost:8000**
Interactive API docs: **http://localhost:8000/docs**

### 6. Run Tests
```bash
# Windows:
run_tests.bat

# Or manually:
python test_pipeline.py
python test_week3_llm.py
python test_api.py
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Service health + API key status |
| `POST` | `/api/generate` | **Primary:** NL prompt → LLM → execute → STL mesh |
| `POST` | `/api/recompute` | Fast parametric recomputation (no LLM, <200ms) |
| `GET` | `/api/admin/models` | List all stored model artifacts |
| `POST` | `/api/admin/cleanup` | Delete stale artifacts older than 1 hour |
| `GET` | `/static/models/{file}` | Download STL/STEP files |

### Example: Generate a Part
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a hollow cylinder with 20mm outer radius and 5mm wall thickness"}'
```

### Example: Recompute with Updated Sliders
```bash
curl -X POST http://localhost:8000/api/recompute \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "part_abc12345",
    "python_code": "PARAMS = {\"outer_radius\": 20.0, ...}\n...",
    "updated_parameters": {"outer_radius": 35.0}
  }'
```

---

## 🧠 Architecture

```
User Prompt (NL)
      │
      ▼
 LLM 3-Tier Fallback
 ├── Gemini 2.0 Flash   ← Primary (best quality)
 ├── Gemini 2.5 Flash   ← Secondary (separate model quota)
 └── Groq Llama-3.3-70B ← Tertiary (always-on fallback)
      │
      ▼
 DualOutputPayload
 ├── python_code (trimesh script with PARAMS block)
 └── parameters  (slider schema for the UI)
      │
      ▼
 CAD Subprocess Executor (isolated Python process)
 │    ├── Success → STL + STEP exported
 │    └── Failure → Self-Correction Loop (up to 3 retries)
      │
      ▼
 API Response → STL mesh_url + parameter sliders
```

---

## 📅 Development Progress

| Week | Status | Deliverable |
|------|--------|-------------|
| W1 | ✅ Done | Project setup, venv, CAD subprocess runner, STL export |
| W2 | ✅ Done | FastAPI server, async execution, artifact cleanup, test suite |
| W3 | ✅ Done | Gemini 2.0/2.5 Flash + Groq LLM service, self-correction loop, Pydantic schemas |
| W4 | 🔜 Next | RAG dataset curation, ChromaDB vector store |
| W5–8 | 📋 Planned | RAG integration, error analysis, optimization |
| W9–11 | 📋 Planned | React + Three.js frontend, WebGL viewer |
| W12–14 | 📋 Planned | Testing, deployment, documentation |
