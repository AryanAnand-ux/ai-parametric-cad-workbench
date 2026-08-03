"""
FastAPI Application Entry Point — AI-Driven Parametric CAD Workbench API
"""
import asyncio
import uuid
import time
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

from config import MODELS_DIR, PORT, HOST, GEMINI_API_KEY
from schemas import (
    GenerateRequest, GenerateResponse,
    RecomputeRequest, RecomputeResponse
)
from services.freecad_runner import CADRunner
from services.exporter import GeometryExporter
from services.cleanup import ArtifactCleanupManager
from services.llm_service import LLMService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cad_workbench.main")

# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI-Driven Parametric CAD Workbench API",
    description=(
        "Natural Language to 3D Solid Modeling Platform. "
        "Generates parametric Python CAD scripts via Gemini 2.0 Flash (primary) "
        "with Gemini 2.5 Flash + Groq Llama-3.3-70B fallback. "
        "Supports sub-200ms slider recomputation and automated self-correction."
    ),
    version="2.0.0"
)

# CORS: allow_credentials requires explicit origins (not wildcard)
# Use ["*"] without credentials for open dev access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,   # Must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/models", StaticFiles(directory=str(MODELS_DIR)), name="models")


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health_check():
    """Returns service health and API key configuration status."""
    return {
        "status": "online",
        "service": "AI-Driven Parametric CAD Workbench",
        "version": "2.0.0",
        "storage_ready": MODELS_DIR.exists(),
        "gemini_configured": bool(GEMINI_API_KEY),   # Use imported config var
        "timestamp": time.time()
    }


# ---------------------------------------------------------------------------
# Primary Generation Endpoint
# ---------------------------------------------------------------------------

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_part(payload: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Primary Generation Endpoint (Week 3 deliverable).

    Flow:
    1. Calls LLM (3-tier fallback) with structured dual-output prompt.
    2. Parses response into DualOutputPayload (python_code + parameters).
    3. Executes CAD script in an isolated subprocess.
    4. Self-correction loop (up to 3 retries) if execution fails.
    5. Returns STL mesh_url, STEP step_url, parameters, and mesh metrics.
    """
    script_id = f"part_{uuid.uuid4().hex[:8]}"
    self_correction_attempts = 0
    model_used = "unknown"

    prompt_preview = payload.prompt[:60] + ("..." if len(payload.prompt) > 60 else "")
    logger.info(f"[GENERATE] script_id={script_id} | prompt='{prompt_preview}'")

    # Step 1: LLM Dual-Output Generation (3-tier fallback)
    try:
        dual_output, model_used = LLMService.generate_dual_output(payload.prompt)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"LLM generation failed (all 3 tiers exhausted): {str(e)}"
        )

    logger.info(
        f"[GENERATE] model={model_used} | part='{dual_output.part_name}' | "
        f"code={len(dual_output.python_code)} chars | {len(dual_output.parameters)} params"
    )

    # Step 2: Execute CAD Script with Self-Correction Loop
    current_code = dual_output.python_code
    execution_result = None

    for attempt in range(LLMService.MAX_RETRIES + 1):
        execution_result = await CADRunner.execute_script_async(
            script_id=script_id,
            python_code=current_code
        )

        if execution_result["status"] == "success":
            break

        if attempt < LLMService.MAX_RETRIES:
            self_correction_attempts += 1
            traceback_text = execution_result.get("stderr", "Unknown execution error")
            logger.warning(
                f"[SELF-CORRECT] Attempt {self_correction_attempts}/{LLMService.MAX_RETRIES} "
                f"for script_id={script_id}"
            )

            try:
                corrected, model_used = LLMService.correct_code(
                    user_prompt=payload.prompt,
                    failed_code=current_code,
                    error_traceback=traceback_text
                )
                current_code = corrected.python_code
                dual_output = corrected
                logger.info(f"[SELF-CORRECT] Corrected via model={model_used}")
            except Exception as correction_error:
                logger.error(f"[SELF-CORRECT] Correction call failed: {correction_error}")
                break
        else:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "CAD script execution failed after all self-correction attempts.",
                    "self_correction_attempts": self_correction_attempts,
                    "last_traceback": execution_result.get("stderr", "")[:500]
                }
            )

    background_tasks.add_task(ArtifactCleanupManager.cleanup_old_artifacts, 86400)

    return GenerateResponse(
        status="success",
        script_id=script_id,
        part_name=dual_output.part_name,
        description=dual_output.description,
        python_code=current_code,
        parameters=dual_output.parameters,
        mesh_url=execution_result.get("mesh_url"),
        step_url=execution_result.get("step_url"),
        mesh_info=execution_result.get("mesh_info"),
        recomputation_time_ms=execution_result.get("recomputation_time_ms"),
        self_correction_attempts=self_correction_attempts,
        model_used=model_used
    )


# ---------------------------------------------------------------------------
# Fast Parametric Recomputation Endpoint
# ---------------------------------------------------------------------------

@app.post("/api/recompute", response_model=RecomputeResponse)
async def recompute_part(payload: RecomputeRequest):
    """
    Fast Parametric Recomputation (<200ms target).
    Injects updated slider values into the PARAMS block and re-executes — NO LLM call.
    """
    result = await CADRunner.execute_script_async(
        script_id=f"{payload.script_id}_recomputed",
        python_code=payload.python_code,
        parameters=dict(payload.updated_parameters)
    )

    if result["status"] == "error":
        raise HTTPException(
            status_code=400,
            detail={"error": "Recomputation failed", "stderr": result.get("stderr", "")}
        )

    return RecomputeResponse(
        status="success",
        script_id=payload.script_id,
        mesh_url=result.get("mesh_url"),
        step_url=result.get("step_url"),
        mesh_info=result.get("mesh_info"),
        recomputation_time_ms=result.get("recomputation_time_ms")
    )


# ---------------------------------------------------------------------------
# Admin Utilities
# ---------------------------------------------------------------------------

@app.post("/api/admin/cleanup")
async def trigger_cleanup():
    """Manually trigger stale artifact cleanup (async-safe)."""
    loop = asyncio.get_event_loop()
    # Run sync blocking I/O in a thread pool to avoid blocking the event loop
    count = await loop.run_in_executor(
        None, ArtifactCleanupManager.cleanup_old_artifacts, 3600   # 1 hour threshold (not 0)
    )
    return {"status": "success", "removed_files": count}


@app.get("/api/admin/models")
async def list_generated_models():
    """List all currently stored 3D model artifacts."""
    files = []
    if MODELS_DIR.exists():
        for f in sorted(MODELS_DIR.iterdir()):
            if f.is_file():
                files.append({
                    "filename": f.name,
                    "size_kb": round(f.stat().st_size / 1024, 2),
                    "url": f"/static/models/{f.name}"
                })
    return {"status": "success", "count": len(files), "models": files}


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
