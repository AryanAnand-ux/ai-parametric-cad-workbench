# AI-Driven Parametric CAD Workbench

> **Natural Language → 3D Solid Model.** Type a description, get an interactive 3D mechanical part in your browser, tune it live with real-time sliders, and export production-ready STL & STEP files.

---

## ⚡ Quick Start (Run Locally in 2 Steps)

### 1. Backend Setup (FastAPI + build123d + RAG)
```bash
# Navigate to backend
cd backend

# Create & activate virtual environment
python -m venv venv
# Windows:
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
> `GROQ_API_KEY=your_key_here` *(optional fallback)*

Run pre-flight check & start server:
```bash
python startup_check.py
python -m uvicorn main:app --reload --port 8000
```
*Backend runs on: **http://localhost:8000** | Interactive Docs: **http://localhost:8000/docs***

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

---

## 🌟 Key System Features

- 🧊 **Real CAD Solid Engine (`build123d` + OpenCASCADE)**: Generates true boundary-representation (B-Rep) solid models with exact CSG operations, fillets, chamfers, and STEP export.
- 🧠 **50-Example RAG Vector Store**: Uses local `sentence-transformers/all-MiniLM-L6-v2` embeddings in ChromaDB to retrieve top-3 CAD code examples for few-shot LLM prompt injection.
- ⚡ **Sub-200ms Parametric Recomputation**: Adjusting UI sliders recompute solid geometry directly via `build123d` without calling the LLM.
- 🛡️ **AST Security Sandbox**: Whitelists only safe imports (`build123d`, `math`, `typing`) before executing any generated script.
- 🎨 **Soft Neobrutalism UI**: Bold outlines, hard drop-shadows, Space Grotesk typography, and a studio blueprint 3D WebGL viewport powered by React Three Fiber.
- 🔄 **Automated Self-Correction Loop**: Catches script errors at runtime and feeds tracebacks back to the LLM (up to 3 retries) for autonomous repair.

---

## 📁 Repository Structure

```
ai-parametric-cad-workbench/
├── README.md                 ← Project Documentation & Setup Guide
├── WEEKLY_PLAN.md            ← 14-Week Development Roadmap & Milestones
├── backend/
│   ├── main.py               ← FastAPI Application & Route Handlers
│   ├── schemas.py            ← Pydantic V2 API Request/Response Schemas
│   ├── config.py             ← Environment Variable & Directory Configuration
│   ├── startup_check.py      ← Pre-flight Dependency & Index Sanity Check
│   ├── requirements.txt      ← Python Dependencies (build123d, chromadb, fastapi, etc.)
│   ├── test_week4_build123d.py ← Engine & RAG Test Suite
│   ├── test_api.py           ← Async API Endpoint Test Suite
│   ├── services/
│   │   ├── cad_runner.py     ← Subprocess Executor & AST Security Sandbox
│   │   ├── rag_service.py    ← ChromaDB Indexing, Embedding, & Retrieval
│   │   ├── llm_service.py    ← 3-Tier LLM Orchestrator (Gemini 2.5 Flash + Fallbacks)
│   │   └── cleanup.py        ← Temporary CAD Artifact Lifecycle Manager
│   └── rag_corpus/
│       ├── examples_week4.py ← First 20 CAD Example Snippets
│       └── examples_week5.py ← 30 Additional Mechanical CAD Snippets (50 Total)
└── frontend/
    ├── index.html            ← Main HTML Template with Space Grotesk Google Fonts
    ├── vite.config.js        ← Vite Config with Backend Proxy (/api & /static)
    ├── package.json          ← Frontend Dependencies (@react-three/fiber, drei, three)
    └── src/
        ├── App.jsx           ← Main React App Shell & State Management
        ├── index.css         ← Soft Neobrutalism Design System
        ├── api.js            ← Axios Client for Backend Endpoints
        └── components/
            ├── Viewer3D.jsx  ← React Three Fiber WebGL Viewer (Orbit Controls, Grid Floor)
            └── ParameterSlider.jsx ← Parametric Slider Control Component
```

---

## 🔌 API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status, storage status, & API key configuration |
| `POST` | `/api/generate` | **Primary:** NL prompt → RAG → LLM → execute → 3D STL + STEP |
| `POST` | `/api/recompute` | Fast parametric slider recomputation (sub-200ms, no LLM call) |
| `GET` | `/api/admin/models` | List all cached 3D STL/STEP model artifacts |
| `POST` | `/api/admin/cleanup` | Remove temporary artifacts older than 1 hour |
| `GET` | `/static/models/{file}` | Serve generated STL preview & STEP download files |

---

## 🧪 Running Automated Tests

```bash
# Run CAD Engine & RAG Retrieval Tests
cd backend
python test_week4_build123d.py

# Run FastAPI Endpoint Tests
python test_api.py

# Run Frontend Production Build Check
cd ../frontend
npm run build
```

---

## 👥 Team & Responsibilities

| Role | Primary Focus |
|---|---|
| **Lead (AI/RAG)** | LLM orchestrator, ChromaDB vector store, RAG prompt injection, self-correction loop |
| **Partner 2 (Backend/Geometry)** | FastAPI endpoints, `build123d` kernel integration, AST security sandbox, artifact cleanup |
| **Partner 3 (Frontend/WebGL)** | React + Vite architecture, React Three Fiber 3D WebGL viewport, Soft Neobrutalism UI design |
