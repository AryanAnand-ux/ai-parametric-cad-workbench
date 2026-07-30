import os
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import MODELS_DIR, PORT, HOST
from services.freecad_runner import CADRunner
from services.exporter import GeometryExporter
from services.cleanup import ArtifactCleanupManager

# Initialize FastAPI Application
app = FastAPI(
    title="AI-Driven Parametric CAD Workbench API",
    description="Natural Language to 3D Solid Modeling Platform API",
    version="1.0.0"
)

# Enable CORS for React frontend cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve 3D model artifacts (STL / STEP)
app.mount("/static/models", StaticFiles(directory=str(MODELS_DIR)), name="models")


# Structured Request / Response Schemas
class ExecuteTestRequest(BaseModel):
    script_id: str = Field(default="part_001", description="Unique part identifier")
    python_code: str = Field(..., description="Python CAD script to execute")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Initial parameters")

class RecomputeRequest(BaseModel):
    script_id: str = Field(..., description="Part script identifier")
    python_code: str = Field(..., description="Existing Python code string")
    updated_parameters: Dict[str, Any] = Field(..., description="Updated parameter dictionary from UI sliders")

class ExecutionResultResponse(BaseModel):
    status: str = Field(..., description="Execution status: 'success' or 'error'")
    script_id: str = Field(..., description="Part identifier")
    recomputation_time_ms: int = Field(..., description="Subprocess execution duration in milliseconds")
    stdout: Optional[str] = Field(None, description="Standard output log")
    stderr: Optional[str] = Field(None, description="Standard error trace log")
    mesh_url: Optional[str] = Field(None, description="Static URL to STL mesh")
    step_url: Optional[str] = Field(None, description="Static URL to STEP solid file")
    mesh_info: Optional[Dict[str, Any]] = Field(None, description="Bounding box & volume metrics")
    python_code: Optional[str] = Field(None, description="Executed Python script with injected parameters")


@app.get("/api/health")
async def health_check():
    """Returns service health status and artifact storage status."""
    return {
        "status": "online",
        "service": "AI-Driven Parametric CAD Workbench",
        "storage_ready": MODELS_DIR.exists(),
        "timestamp": time.time()
    }


@app.post("/api/execute-test", response_model=ExecutionResultResponse)
async def execute_test(payload: ExecuteTestRequest, background_tasks: BackgroundTasks):
    """
    Executes a CAD script asynchronously in an isolated subprocess.
    """
    result = await CADRunner.execute_script_async(
        script_id=payload.script_id,
        python_code=payload.python_code,
        parameters=payload.parameters
    )
    
    # Schedule artifact cleanup in background
    background_tasks.add_task(ArtifactCleanupManager.cleanup_old_artifacts, 86400)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result)
        
    return result


@app.post("/api/recompute", response_model=ExecutionResultResponse)
async def recompute_part(payload: RecomputeRequest):
    """
    Fast Parametric Recomputation Endpoint (<200ms target).
    Directly updates parameter dictionary header and re-executes CAD runner in an isolated non-blocking subprocess.
    """
    result = await CADRunner.execute_script_async(
        script_id=f"{payload.script_id}_recomputed",
        python_code=payload.python_code,
        parameters=payload.updated_parameters
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result)
        
    return result


@app.post("/api/admin/cleanup")
async def trigger_cleanup():
    """Manual endpoint to trigger stale file artifact cleanup."""
    count = ArtifactCleanupManager.cleanup_old_artifacts(max_age_seconds=0)
    return {"status": "success", "removed_files": count}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
