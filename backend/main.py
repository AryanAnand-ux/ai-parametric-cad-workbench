"""
FastAPI Application Entry Point — AI-Driven Parametric CAD Workbench API
"""
import asyncio
import re
import uuid
import time
import logging
from pathlib import Path
from collections import defaultdict
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

from config import (
    MODELS_DIR, PORT, HOST, GEMINI_API_KEY, GEMINI_WEB_ENABLED,
    ADMIN_TOKEN, ALLOWED_ORIGINS, RELOAD, ENVIRONMENT, RAG_BUILD_ON_STARTUP,
)
from schemas import (
    GenerateRequest, GenerateResponse,
    RecomputeRequest, RecomputeResponse,
    ModifyRequest, ModifyResponse,
)
from services.cad_runner import CADRunner, is_safe_script_id
from services.cleanup import ArtifactCleanupManager
from services.llm_service import LLMService
from services.rag_service import RAGService
from services import gemini_web_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cad_workbench.main")

_modify_id_lock = asyncio.Lock()
_reserved_modify_ids: set[str] = set()


class SimpleRateLimiter:
    """Sliding-window per-IP rate limiter."""
    def __init__(self, requests_per_minute: int):
        self.rpm = requests_per_minute
        self.history = defaultdict(list)
        self.lock = asyncio.Lock()

    async def check(self, client_ip: str):
        now = time.time()
        cutoff = now - 60.0
        async with self.lock:
            timestamps = [t for t in self.history[client_ip] if t > cutoff]
            if len(timestamps) >= self.rpm:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Maximum {self.rpm} requests per minute allowed."
                )
            timestamps.append(now)
            self.history[client_ip] = timestamps


generate_limiter = SimpleRateLimiter(requests_per_minute=10)
modify_limiter = SimpleRateLimiter(requests_per_minute=10)
recompute_limiter = SimpleRateLimiter(requests_per_minute=40)


def require_admin_token(provided_token: str | None) -> None:
    """Require admin authentication in production and when a token is configured."""
    if ADMIN_TOKEN and provided_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Admin authentication required.")
    if ENVIRONMENT != "development" and not ADMIN_TOKEN:
        raise HTTPException(status_code=503, detail="Admin authentication is not configured.")


async def allocate_modify_script_id(
    base_id: str,
    models_dir,
    reserved_ids: set[str] | None = None,
    lock: asyncio.Lock | None = None,
) -> str:
    """Reserve the next version ID without allowing concurrent collisions."""
    active_lock = lock or _modify_id_lock
    active_reserved = reserved_ids if reserved_ids is not None else _reserved_modify_ids
    async with active_lock:
        version_num = 1
        while True:
            candidate = f"{base_id}_v{version_num}"
            if candidate not in active_reserved and not (models_dir / f"{candidate}.py").exists():
                active_reserved.add(candidate)
                return candidate
            version_num += 1

# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI-Driven Parametric CAD Workbench API",
    description=(
        "Natural Language to 3D Solid Modeling Platform. "
        "Generates parametric Python CAD scripts via Gemini Multi-Model Fallback "
        "(gemini-3.5-flash-lite -> gemini-flash-lite-latest -> gemini-3.1-flash-lite -> Groq Llama-3.3-70B). "
        "Supports sub-200ms slider recomputation and automated self-correction."
    ),
    version="2.0.0"
)

# CORS: allow_credentials requires explicit origins (not wildcard)
# Use ["*"] without credentials for open dev access
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,   # Must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Verify production security requirements and initialize RAG."""
    if ENVIRONMENT == "production" and not ADMIN_TOKEN:
        logger.critical("[FATAL] ENVIRONMENT is set to 'production' but ADMIN_TOKEN is not configured.")
        raise RuntimeError("ADMIN_TOKEN environment variable must be set when running in production mode.")

    if not RAG_BUILD_ON_STARTUP:
        logger.info("[STARTUP] RAG startup indexing disabled; retrieval will use any existing index.")
        return
    try:
        count = RAGService.build_index()
        total = RAGService.index_size()
        logger.info(f"[STARTUP] RAG index ready: {count} new docs added, {total} total stored in ChromaDB.")
    except Exception as e:
        logger.error(f"[STARTUP] Failed to initialize RAG index: {e}")


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
        "gemini_web_configured": bool(gemini_web_client.is_configured()),
        "timestamp": time.time()
    }


def require_artifact_access(filename: str, provided_token: str | None) -> Path:
    """Resolve a public mesh artifact while keeping generated Python source protected."""
    path = Path(filename)
    if path.name != filename or path.suffix.lower() not in {".stl", ".step"} and path.suffix.lower() != ".py":
        raise HTTPException(status_code=404, detail="Artifact not found.")
    if not is_safe_script_id(path.stem):
        raise HTTPException(status_code=404, detail="Artifact not found.")
    if path.suffix.lower() == ".py":
        require_admin_token(provided_token)
    artifact_path = MODELS_DIR / filename
    if not artifact_path.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found.")
    return artifact_path


@app.get("/static/models/{filename:path}")
async def serve_model_artifact(filename: str, x_admin_token: str | None = Header(default=None)):
    """Serve preview/download artifacts without exposing source code publicly."""
    return FileResponse(path=str(require_artifact_access(filename, x_admin_token)))


# ---------------------------------------------------------------------------
# Primary Generation Endpoint
# ---------------------------------------------------------------------------

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_part(payload: GenerateRequest, background_tasks: BackgroundTasks, request: Request):
    """
    Primary Generation Endpoint (Week 3 deliverable).

    Flow:
    1. Calls LLM (3-tier fallback) with structured dual-output prompt.
    2. Parses response into DualOutputPayload (python_code + parameters).
    3. Executes CAD script in an isolated subprocess.
    4. Self-correction loop (up to 3 retries) if execution fails.
    5. Returns STL mesh_url, STEP step_url, parameters, and mesh metrics.
    """
    client_ip = request.client.host if request.client else "unknown"
    await generate_limiter.check(client_ip)

    script_id = f"part_{uuid.uuid4().hex[:8]}"
    self_correction_attempts = 0
    model_used = "unknown"

    prompt_preview = payload.prompt[:60] + ("..." if len(payload.prompt) > 60 else "")
    logger.info(f"[GENERATE] script_id={script_id} | prompt='{prompt_preview}'")

    # Step 1: LLM Dual-Output Generation (3-tier fallback, run non-blocking in thread pool)
    try:
        dual_output, model_used = await asyncio.to_thread(
            LLMService.generate_dual_output, payload.prompt
        )
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
            python_code=current_code,
            design_mode=dual_output.design_mode,
            component_names=dual_output.components,
        )

        is_geo_valid = execution_result.get("mesh_info", {}).get("is_valid", True)
        if execution_result["status"] == "success" and is_geo_valid:
            break

        if attempt < LLMService.MAX_RETRIES:
            self_correction_attempts += 1
            if execution_result["status"] != "success":
                traceback_text = execution_result.get("stderr", "Unknown execution error")
            else:
                warnings = execution_result.get("mesh_info", {}).get("geometry_warnings", [])
                traceback_text = "GEOMETRY TOPOLOGY VALIDATION FAILURE:\n" + "\n".join(warnings)

            logger.warning(
                f"[SELF-CORRECT] Attempt {self_correction_attempts}/{LLMService.MAX_RETRIES} "
                f"for script_id={script_id} | reason={traceback_text[:120].strip()!r}"
            )

            try:
                corrected, model_used = await asyncio.to_thread(
                    LLMService.correct_code,
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

    # If execution still failed after retries or early break, raise HTTPException
    is_geo_valid = execution_result.get("mesh_info", {}).get("is_valid", True) if execution_result else False
    if not execution_result or execution_result.get("status") != "success" or not is_geo_valid:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "CAD script execution or geometry topology failed after all self-correction attempts.",
                "self_correction_attempts": self_correction_attempts,
                "error_code": execution_result.get("error_type", "cad_execution_failed") if execution_result else "cad_execution_failed",
                "geometry_warnings": execution_result.get("mesh_info", {}).get("geometry_warnings", []) if execution_result else [],
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
        design_mode=dual_output.design_mode,
        components=dual_output.components,
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
async def recompute_part(payload: RecomputeRequest, request: Request = None):
    """
    Fast Parametric Recomputation (<200ms target).
    Injects updated slider values into the PARAMS block and re-executes — NO LLM call.
    """
    if request:
        client_ip = request.client.host if request.client else "unknown"
        await recompute_limiter.check(client_ip)

    t0 = time.perf_counter()
    execution_id = f"{payload.script_id}_recomputed_{uuid.uuid4().hex[:10]}"
    result = await CADRunner.execute_script_async(
        script_id=execution_id,
        python_code=payload.python_code,
        parameters=dict(payload.updated_parameters),
        design_mode=payload.design_mode,
        component_names=payload.components,
        fast_preview=True,
    )
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    mesh_info = result.get("mesh_info") or {}
    # For recomputation, accept the mesh if execution succeeded and produced any
    # geometry (volume > 0). Non-watertight meshes from complex boolean operations
    # are still renderable and useful — don't block slider updates for topology issues.
    exec_ok = result.get("status") == "success"
    has_geometry = (
        (mesh_info.get("volume_mm3", 0) or 0) > 0
        or bool(mesh_info.get("face_count", 0))
        or bool(mesh_info.get("dimensions_mm"))
        or (mesh_info.get("is_valid") is True and bool(result.get("mesh_url")))
    )
    explicit_invalid = mesh_info.get("is_valid") is False
    if not exec_ok or not has_geometry or explicit_invalid:
        logger.warning(f"[RECOMPUTE] Failed for {payload.script_id} in {elapsed_ms}ms: {result.get('stderr', '')[:200]}")
        error_message = (
            "Recomputation failed - CAD script produced invalid geometry"
            if explicit_invalid
            else "Recomputation failed - CAD script did not produce geometry"
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error": error_message,
                "error_code": result.get("error_type", "cad_execution_failed"),
                "stderr_snippet": result.get("stderr", "")[:300],
                "geometry_warnings": mesh_info.get("geometry_warnings", []),
            }
        )

    dims = mesh_info.get("dimensions_mm", {})
    logger.info(
        f"[RECOMPUTE] Success | script_id={payload.script_id} | "
        f"time={elapsed_ms}ms | dims={dims}"
    )

    return RecomputeResponse(
        status="success",
        script_id=payload.script_id,
        mesh_url=result.get("mesh_url"),
        step_url=result.get("step_url"),
        mesh_info=mesh_info,
        recomputation_time_ms=elapsed_ms,
        design_mode=payload.design_mode,
        components=payload.components,
    )


# ---------------------------------------------------------------------------
# Admin Utilities
# ---------------------------------------------------------------------------

@app.post("/api/admin/cleanup")
async def trigger_cleanup(x_admin_token: str | None = Header(default=None)):
    """Manually trigger stale artifact cleanup (async-safe)."""
    require_admin_token(x_admin_token)
    loop = asyncio.get_event_loop()
    # Run sync blocking I/O in a thread pool to avoid blocking the event loop
    count = await loop.run_in_executor(
        None, ArtifactCleanupManager.cleanup_old_artifacts, 3600   # 1 hour threshold (not 0)
    )
    return {"status": "success", "removed_files": count}


@app.get("/api/admin/models")
async def list_generated_models(x_admin_token: str | None = Header(default=None)):
    """List all currently stored 3D model artifacts."""
    require_admin_token(x_admin_token)
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


@app.get("/api/script/{script_id}")
async def get_script_code(script_id: str, x_admin_token: str | None = Header(default=None)):
    """Retrieve raw build123d Python script code for a generated model by script_id."""
    require_admin_token(x_admin_token)
    if not is_safe_script_id(script_id):
        raise HTTPException(status_code=400, detail="Invalid script identifier.")
    py_path = MODELS_DIR / f"{script_id}.py"
    if not py_path.exists():
        raise HTTPException(status_code=404, detail=f"Script '{script_id}' not found.")
    try:
        with open(py_path, "r", encoding="utf-8") as f:
            code = f.read()
        return {"status": "success", "script_id": script_id, "code": code}
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Could not read script file: {e}")


# ---------------------------------------------------------------------------
# Download Endpoint
# ---------------------------------------------------------------------------

@app.get("/api/download/{script_id}/{fmt}")
async def download_model(
    script_id: str,
    fmt: str,
    x_admin_token: str | None = Header(default=None),
):
    """
    Download production-ready CAD artifacts (STEP / STL / PY).
    Returns a FileResponse with appropriate attachment headers.
    """
    from fastapi.responses import FileResponse

    if not is_safe_script_id(script_id):
        raise HTTPException(status_code=400, detail="Invalid script identifier.")
    
    fmt_lower = fmt.lower().strip(".")
    allowed_formats = {"stl": "application/sla", "step": "application/step", "stp": "application/step"}
    
    if fmt_lower not in allowed_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{fmt}'. Public formats: stl, step, stp. For Python source code, use GET /api/script/{script_id} with admin authentication."
        )
        
    ext = "step" if fmt_lower in ("step", "stp") else fmt_lower
    file_path = MODELS_DIR / f"{script_id}.{ext}"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Artifact '{script_id}.{ext}' not found on server."
        )
        
    media_type = allowed_formats[fmt_lower]
    download_filename = f"{script_id}.{ext}"
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=download_filename,
        headers={"Content-Disposition": f'attachment; filename="{download_filename}"'}
    )




@app.post("/api/modify", response_model=ModifyResponse)
async def modify_part(payload: ModifyRequest, background_tasks: BackgroundTasks, request: Request):
    """
    Chat-to-Modify Endpoint (Week 7 deliverable).

    Takes an existing build123d script and a natural language change request.
    Returns a fully updated GenerateResponse-compatible payload (new code, parameters, STL/STEP).

    Flow:
    1. LLMService.modify_code() — edits the script via the LLM using MODIFY_PROMPT_TEMPLATE.
    2. CADRunner executes the updated script.
    3. Self-correction loop (up to 3 retries) on execution failure.
    4. Returns updated STL mesh_url, STEP step_url, parameters, and mesh metrics.
    """
    client_ip = request.client.host if request.client else "unknown"
    await modify_limiter.check(client_ip)

    # Generate a versioned script_id to preserve original
    base_id = re.sub(r'_v\d+$', '', payload.script_id)   # Strip existing _v1, _v2 suffix
    # Count existing versions
    new_script_id = await allocate_modify_script_id(base_id, MODELS_DIR)

    modification_preview = payload.modification_prompt[:60] + (
        "..." if len(payload.modification_prompt) > 60 else ""
    )
    logger.info(
        f"[MODIFY] script_id={new_script_id} | base={base_id} | "
        f"request='{modification_preview}'"
    )

    model_used = "unknown"
    self_correction_attempts = 0

    # Step 1: LLM Modification
    try:
        dual_output, model_used = await asyncio.to_thread(
            LLMService.modify_script,
            python_code=payload.python_code,
            modification_prompt=payload.modification_prompt,
            part_name=payload.part_name,
            parameters=payload.parameters,
            design_mode=payload.design_mode,
            components=payload.components,
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"LLM modification failed: {str(e)}"
        )

    logger.info(
        f"[MODIFY] model={model_used} | part='{dual_output.part_name}' | "
        f"code={len(dual_output.python_code)} chars | {len(dual_output.parameters)} params"
    )

    # Step 2: Execute with Self-Correction Loop
    current_code = dual_output.python_code
    execution_result = None

    for attempt in range(LLMService.MAX_RETRIES + 1):
        execution_result = await CADRunner.execute_script_async(
            script_id=new_script_id,
            python_code=current_code,
            design_mode=dual_output.design_mode,
            component_names=dual_output.components,
        )

        is_geo_valid = execution_result.get("mesh_info", {}).get("is_valid", True)
        if execution_result["status"] == "success" and is_geo_valid:
            break

        if attempt < LLMService.MAX_RETRIES:
            self_correction_attempts += 1
            if execution_result["status"] != "success":
                traceback_text = execution_result.get("stderr", "Unknown execution error")
            else:
                warnings = execution_result.get("mesh_info", {}).get("geometry_warnings", [])
                traceback_text = "GEOMETRY TOPOLOGY VALIDATION FAILURE:\n" + "\n".join(warnings)

            logger.warning(
                f"[MODIFY-CORRECT] Attempt {self_correction_attempts}/{LLMService.MAX_RETRIES} "
                f"for script_id={new_script_id} | reason={traceback_text[:120].strip()!r}"
            )
            try:
                corrected, model_used = await asyncio.to_thread(
                    LLMService.correct_code,
                    user_prompt=payload.modification_prompt,
                    failed_code=current_code,
                    error_traceback=traceback_text
                )
                current_code = corrected.python_code
                dual_output = corrected
            except Exception as correction_error:
                logger.error(f"[MODIFY-CORRECT] Correction call failed: {correction_error}")
                break

    is_geo_valid = execution_result.get("mesh_info", {}).get("is_valid", True) if execution_result else False
    if not execution_result or execution_result.get("status") != "success" or not is_geo_valid:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Modified CAD script execution or geometry topology failed after all self-correction attempts.",
                "self_correction_attempts": self_correction_attempts,
                "error_code": execution_result.get("error_type", "cad_execution_failed") if execution_result else "cad_execution_failed",
                "geometry_warnings": execution_result.get("mesh_info", {}).get("geometry_warnings", []) if execution_result else [],
            }
        )

    background_tasks.add_task(ArtifactCleanupManager.cleanup_old_artifacts, 86400)

    return ModifyResponse(
        status="success",
        script_id=new_script_id,
        part_name=dual_output.part_name,
        description=dual_output.description,
        python_code=current_code,
        parameters=dual_output.parameters,
        design_mode=dual_output.design_mode,
        components=dual_output.components,
        mesh_url=execution_result.get("mesh_url"),
        step_url=execution_result.get("step_url"),
        mesh_info=execution_result.get("mesh_info"),
        recomputation_time_ms=execution_result.get("recomputation_time_ms"),
        model_used=model_used,
        modification_summary=payload.modification_prompt,
    )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=RELOAD)

