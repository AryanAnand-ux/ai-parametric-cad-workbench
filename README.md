# 🛠️ AI-Driven Parametric CAD Workbench
> **A Natural Language to 3D Solid Modeling Platform via Headless CAD Execution & WebGL**

---

## 📌 Project Overview
The **AI-Driven Parametric CAD Workbench** bridges LLMs, Retrieval-Augmented Generation (RAG), and a headless Python geometry engine (FreeCAD / CadQuery) to synthesize editable 3D mechanical parts from plain English prompts.

### Key Technical Innovations
- **Dual-Output AI Generation:** LLM outputs both executable Python CAD code and a structured JSON parameter schema.
- **Zero-Latency Slider Recomputation:** UI slider changes bypass the LLM and re-run the backend geometry engine directly in $<200\text{ ms}$.
- **Self-Correction Execution Loop:** Traps Python subprocess execution errors and automatically re-prompts the LLM to fix syntax or geometric bugs.
- **Industry Standard Exports:** Supports `.stl` (for WebGL and 3D printing) and `.step` (for solid CAD modeling).

---

## 🏗️ Repository Structure
```
d:/Projects/Minor_project/
├── WEEKLY_PLAN.md               # 14-Week detailed execution roadmap
├── README.md                    # Project README and quick start
├── .gitignore                   # Git ignore patterns
└── backend/
    ├── config.py                # System paths and configuration
    ├── main.py                  # FastAPI application entry point
    ├── requirements.txt         # Dependencies manifest
    ├── test_pipeline.py         # Subprocess pipeline test suite
    ├── test_api.py              # FastAPI async route test suite
    ├── services/
    │   ├── freecad_runner.py    # Async CAD runner & parameter injector
    │   ├── exporter.py          # 3D mesh inspection & exporter
    │   └── cleanup.py           # Temporary artifact cleanup manager
    └── temp/
        └── models/              # Static generated 3D models
```

---

## 👥 3-Member Team Task Breakdown

| Team Member | Role | Focus Area & Deliverables |
| :--- | :--- | :--- |
| **Partner 1 (Lead)** | **AI & RAG Specialist** | Gemini 1.5 Dual-Output parser, ChromaDB vector store, system prompts, self-correction execution loop. |
| **Partner 2** | **Backend & Geometry Specialist** | CAD script macro library, STEP/STL export engine, fast `/api/recompute` optimization, execution benchmarking. |
| **Partner 3** | **Frontend & WebGL Specialist** | React 18 + Vite dashboard, `@react-three/fiber` 3D Canvas, dynamic parameter sliders, code viewer drawer. |

---

## 🚀 Quick Start Guide

### 1. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create & activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Run backend tests
python test_pipeline.py
python test_api.py

# Launch FastAPI development server
python main.py
```

### 2. API Endpoints
- `GET /api/health`: Check service readiness.
- `POST /api/execute-test`: Execute a Python CAD script in an isolated subprocess.
- `POST /api/recompute`: Fast parametric slider recomputation endpoint.
- `POST /api/admin/cleanup`: Trigger artifact garbage collection.
- `GET /static/models/{filename}`: Static 3D model download route.
