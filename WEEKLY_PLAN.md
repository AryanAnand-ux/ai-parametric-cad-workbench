# 🛠️ AI-Driven Parametric CAD Workbench
## 📅 14-Week Comprehensive Project Execution Plan

> **Project Title:** AI-Driven Parametric CAD Workbench  
> **Core Concept:** A Natural Language to 3D Solid Modeling Platform via Headless CAD Execution (FreeCAD / CadQuery) & WebGL (Three.js / React)  
> **Key Innovation:** Dual-Output LLM Generation (Code + Parameter Schema), Sub-200ms Slider Recomputation (Bypassing LLM), Self-Correction Execution Loop, and STEP/STL Industry Exports.

---

## 🏗️ System Architecture & Technology Stack

```
                              USER INTERFACE (React 18 + Vite + TypeScript)
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────┐    ┌───────────────────────────┐    ┌─────────────────────┐  │
│  │ Prompt & Chat Input Panel │    │ Dynamic Parametric Sliders│    │ Three.js 3D Canvas  │  │
│  └─────────────┬─────────────┘    └─────────────┬─────────────┘    └──────────▲──────────┘  │
└────────────────│────────────────────────────────│─────────────────────────────│─────────────┘
                 │ (Text Prompt)                  │ (Updated PARAMS Payload)    │ (STL / GLB)
                 ▼                                ▼                             │
┌───────────────────────────────────────────────────────────────────────────────┴─────────────┐
│                               FASTAPI BACKEND SERVICE                                      │
│                                                                                             │
│  ┌─────────────────────────────────┐           ┌─────────────────────────────────────────┐  │
│  │ RAG & LLM Orchestration Layer   │           │ Parametric Recomputation Engine         │  │
│  │ - Gemini 1.5 Pro/Flash API      │           │ - Injects new PARAMS dictionary header  │  │
│  │ - ChromaDB Doc Vector Search    │           │ - Zero LLM call, <150ms recompute       │  │
│  └────────────────┬────────────────┘           └────────────────────┬────────────────────┘  │
│                   │                                                 │                       │
│                   └────────────────────────┬────────────────────────┘                       │
│                                            │                                                │
│                                            ▼                                                │
│                        ┌──────────────────────────────────────┐                             │
│                        │ Headless CAD Execution Subprocess    │                             │
│                        │ - Runs in background (FreeCAD/CadQuery)│                           │
│                        │ - Self-Correction loop on stderr fail│                             │
│                        └───────────────────┬──────────────────┘                             │
│                                            │                                                │
│                                            ▼                                                │
│                        ┌──────────────────────────────────────┐                             │
│                        │ Mesh & Geometry Exporter             │                             │
│                        │ - Exports .STL, .GLB, and .STEP      │                             │
│                        └──────────────────────────────────────┘                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📅 Detailed Weekly Roadmap (14 Weeks)

### 🔹 Phase 1: Environment Setup & Core Subprocess Engine (Weeks 1 – 3)

#### 📍 Week 1: Project & Repository Initialization
- **Tasks:**
  - Initialize Git workspace with `/backend` and `/frontend` directories.
  - Setup Python 3.10+ virtual environment and install backend core dependencies (`fastapi`, `uvicorn`, `pydantic`, `cadquery`, `trimesh`).
  - Configure FreeCAD environment paths / python bindings fallback setup (`FreeCADCmd` / `CadQuery` dual engine strategy).
  - Create standard directory hierarchy for static generated artifacts (`/backend/temp/`).
- **Deliverables:**
  - Standardized project directory structure.
  - Standalone script verifying background execution and headless `.stl` / `.step` file export from Python.

#### 📍 Week 2: FastAPI CAD Subprocess & Execution Pipeline
- **Tasks:**
  - Build core FastAPI application server with CORS policy and async routing.
  - Develop `freecad_runner.py` service module that accepts Python code strings, writes them safely to temporary files, and executes them in isolated subprocesses.
  - Implement execution timeout limits (e.g., 10-second threshold) and process cleanup routines to prevent memory leakage.
  - Add `/api/health` and basic file serving static routes.
- **Deliverables:**
  - Functional FastAPI service executing raw CAD Python code and serving generated `.stl` mesh URLs.

#### 📍 Week 3: LLM Integration & Dual-Output Schema Definition
- **Tasks:**
  - Integrate Gemini 1.5 API client with structured JSON output settings (`response_mime_type="application/json"`).
  - Define Pydantic models for the **Dual Output Payload**:
    - `python_code`: Executable Python CAD script with standardized `PARAMS = {...}` dictionary.
    - `parameters`: Array of configurable parameters (`name`, `label`, `default`, `min`, `max`, `step`, `type`).
  - Test zero-shot prompt generation for basic primitives (box, cylinder, cone, sphere, hollow pipe).
- **Deliverables:**
  - Reliable LLM service producing valid dual-output payloads matching the schema.

---

### 🔹 Phase 2: RAG Knowledge Base & Self-Correction Engine (Weeks 4 – 6)

#### 📍 Week 4: RAG Dataset Curation & Vector Store Setup
- **Tasks:**
  - Collect official API documentation for `Part` primitives, vector mathematics, placements, boolean operations (`cut`, `fuse`, `common`), and features (`fillet`, `chamfer`).
  - Curate 25 high-quality, pre-validated CAD Python macros demonstrating parametric variable scoping (`PARAMS` header) and offset placement logic.
  - Set up ChromaDB vector database and chunk/embed curated documents using Gemini/SentenceTransformer embeddings.
- **Deliverables:**
  - Ingested ChromaDB vector database containing indexed CAD API reference manuals and benchmark macros.

#### 📍 Week 5: Prompt Engineering & Retrieval Integration
- **Tasks:**
  - Build RAG query pipeline using ChromaDB to retrieve top-$k$ relevant macro snippets based on user prompt intent.
  - Construct specialized system prompts instructing LLM on proper CSG construction techniques (center-offset calculation, vector alignment).
  - Enforce standard `PARAMS = {...}` dictionary injection at the top of every generated script.
- **Deliverables:**
  - RAG-augmented generation pipeline consistently producing syntactically correct parametric scripts.

#### 📍 Week 6: Self-Correction Loop Development
- **Tasks:**
  - Wrap script execution inside FastAPI with error capture (`try/except` capturing `stderr` and `traceback`).
  - Implement multi-turn re-prompting loop: if execution fails, feed broken code + traceback error log back to Gemini for automated patching.
  - Set maximum retry ceiling (3 automated attempts) before failing gracefully.
- **Deliverables:**
  - Automated self-correction engine capable of auto-fixing minor syntax or geometric calculation errors.

---

### 🔹 Phase 3: Mid-Semester Evaluation & Buffer (Weeks 7 – 8)

#### 📍 Week 7: Mid-Term Evaluation & Progress Documentation
- **Tasks:**
  - Compile comprehensive Mid-Semester Progress Report (Architecture, Methodology, Initial Benchmarks).
  - Prepare CLI / API terminal demo showcasing natural language prompt processing $\rightarrow$ Dual Output $\rightarrow$ Automated Execution $\rightarrow$ Valid `.stl`/`.step` generation.
  - Present progress to project guides and evaluators.
- **Deliverables:**
  - Mid-Semester Report & Working CLI backend demo.

#### 📍 Week 8: Buffer & Edge Case Refinement
- **Tasks:**
  - Address feedback from mid-term evaluation.
  - Test prompt boundary cases (e.g., negative dimensions, zero-radius holes, overlapping boolean cuts).
  - Optimize ChromaDB top-$k$ parameters to keep context prompt concise and fast.
- **Deliverables:**
  - Hardened backend engine with improved error handling for invalid geometry inputs.

---

### 🔹 Phase 4: React UI, WebGL Viewport & Parametric Controls (Weeks 9 – 11)

#### 📍 Week 9: React + Three.js 3D Viewport Development
- **Tasks:**
  - Initialize React 18 + Vite + TypeScript frontend application with Tailwind CSS and Lucide Icons.
  - Integrate `@react-three/fiber` and `@react-three/drei` standard 3D canvas viewport.
  - Implement `STLLoader` with vertex normal recalculation for smooth CAD surface shading.
  - Add viewport controls: OrbitControls, bounding box overlay, CAD grid floor, perspective/orthographic view toggle, lighting setups, and camera reset button.
- **Deliverables:**
  - High-performance, interactive 3D WebGL viewport in the React frontend.

#### 📍 Week 10: Dynamic Parametric Slider Panel & Sub-200ms Recomputation
- **Tasks:**
  - Build dynamic React `SliderPanel` component that parses the LLM's `parameters` JSON array and renders input sliders (`min`, `max`, `step`, `default`).
  - Implement `/api/recompute` backend endpoint: accepts `script_id` and updated `PARAMS` values, performs regex string header injection, and re-executes CAD runner directly (bypassing LLM).
  - Implement debounced state updates on the frontend to trigger fast recomputations while user drags sliders.
- **Deliverables:**
  - Real-time interactive UI sliders updating the 3D WebGL mesh on-the-fly in under 200ms.

#### 📍 Week 11: Prompt Chat Panel, Code Inspector & File Exporters
- **Tasks:**
  - Build `ChatPanel` component for entering natural language design prompts with history and status indicators (Generating, Self-Correcting, Ready).
  - Build collapsible `CodeDrawer` component allowing users to view and copy generated Python CAD code.
  - Add download buttons for `.stl` (3D printing), `.step` (CAD modeling), and `.py` (CAD script macro).
- **Deliverables:**
  - Complete, end-to-end web dashboard linking prompt input, 3D viewport, parameter sliders, code viewer, and export handlers.

---

### 🔹 Phase 5: Testing, Benchmarking & Final Viva Defense (Weeks 12 – 14)

#### 📍 Week 12: System Benchmarking & Latency Performance Tuning
- **Tasks:**
  - Evaluate platform across 20 benchmark mechanical parts (e.g., mounting bracket, spur gear, hollow box with lid, pipe flange, step pulley).
  - Measure performance metrics:
    - **Generation Latency:** Initial LLM generation time ($<3\text{s}$).
    - **Recomputation Latency:** Slider update time ($<200\text{ms}$).
    - **Self-Correction Recovery Rate:** Percentage of execution errors auto-resolved ($>60\%$).
    - **First-Pass Execution Accuracy:** Code validity ($>85\%$).
  - Refine UI animations, glassmorphism aesthetics, dark mode, and loading state visual cues.
- **Deliverables:**
  - Comprehensive benchmark dataset and fully polished web application.

#### 📍 Week 13: Final Documentation, Video Demo & Presentation Prep
- **Tasks:**
  - Complete Final Minor Project Report (Abstract, Literature Survey, System Architecture, Methodologies, Results, Future Scope).
  - Record a 2-minute high-resolution video walkthrough demonstrating real-time parameter tweaking and STEP file export into external CAD tools (SolidWorks / Fusion 360).
  - Design slides for final defense presentation.
- **Deliverables:**
  - Final Project Report, Video Demo, and Viva Presentation Deck.

#### 📍 Week 14: Final Defense & Viva Demonstration
- **Tasks:**
  - Deploy final system locally or to cloud instance.
  - Conduct live demonstration during college minor project viva.
  - Field questions from evaluators and project committee.
- **Deliverables:**
  - Successful project defense and final project submission.

---

## 📊 Summary of Weekly Milestones

| Phase | Weeks | Focus Area | Key Output / Milestone |
| :--- | :--- | :--- | :--- |
| **Phase 1** | W1 – W3 | Environment & Core Pipeline | Backend FastAPI executing CAD scripts & LLM dual output setup |
| **Phase 2** | W4 – W6 | RAG & Self-Correction | Vector store ingestion & automated code self-patching loop |
| **Phase 3** | W7 – W8 | Mid-Sem Evaluation | Mid-semester defense & edge-case hardening |
| **Phase 4** | W9 – W11 | Web UI & WebGL Viewport | React frontend with R3F canvas, sub-200ms sliders & STEP exports |
| **Phase 5** | W12 – W14 | Benchmarking & Final Viva | System benchmarks, final report, video demo & project defense |
