"""
Pydantic Schemas for the AI-Driven Parametric CAD Workbench.

Defines the Dual-Output API contract:
  - CADParameter: A single configurable parameter (slider) extracted by the LLM.
  - DualOutputPayload: The full LLM response containing executable code + parameter schema.
  - GenerateRequest / GenerateResponse: /api/generate endpoint contracts.
  - RecomputeRequest / RecomputeResponse: /api/recompute endpoint contracts.
"""
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Core Parameter Schema
# ---------------------------------------------------------------------------

class CADParameter(BaseModel):
    """
    Represents a single configurable design variable exposed as a UI slider.
    The LLM must output an array of these alongside the generated code.
    """
    name: str = Field(
        ...,
        description="Python variable name as it appears in the PARAMS dict (e.g. 'bracket_length')"
    )
    label: str = Field(
        ...,
        description="Human-readable label shown in the UI (e.g. 'Bracket Length (mm)')"
    )
    type: Literal["number", "integer"] = Field(
        default="number",
        description="Parameter data type"
    )
    default: float = Field(
        ...,
        description="Default starting value"
    )
    min: float = Field(
        ...,
        description="Minimum allowed value"
    )
    max: float = Field(
        ...,
        description="Maximum allowed value"
    )
    step: float = Field(
        default=1.0,
        description="Slider step increment"
    )


# ---------------------------------------------------------------------------
# Dual-Output Payload (LLM Response Schema)
# ---------------------------------------------------------------------------

class DualOutputPayload(BaseModel):
    """
    The structured JSON payload the LLM must produce.
    Contains BOTH the executable Python CAD script AND the parameter schema.
    This is the core innovation: a single LLM call outputs everything needed.
    """
    python_code: str = Field(
        ...,
        description=(
            "Complete, executable Python script targeting trimesh/FreeCAD Part API. "
            "MUST begin with a PARAMS = {...} dictionary block containing all tunable variables. "
            "MUST write the output STL mesh to the OUTPUT_STL variable provided by the runtime."
        )
    )
    parameters: List[CADParameter] = Field(
        ...,
        description="Array of CADParameter objects matching the PARAMS dictionary keys in python_code",
        min_length=1
    )
    part_name: str = Field(
        ...,
        description="Short descriptive name for the generated part (e.g. 'Mounting Bracket')"
    )
    description: str = Field(
        ...,
        description="One-sentence description of the generated part and its key design features"
    )


# ---------------------------------------------------------------------------
# API Request / Response Models
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    """Request payload for POST /api/generate"""
    prompt: str = Field(
        ...,
        description="Natural language description of the 3D part to generate",
        min_length=5
    )


class GenerateResponse(BaseModel):
    """Response payload for POST /api/generate"""
    status: str
    script_id: str
    part_name: str
    description: str
    python_code: str
    parameters: List[CADParameter]
    mesh_url: Optional[str] = None
    step_url: Optional[str] = None
    mesh_info: Optional[Dict[str, Any]] = None
    recomputation_time_ms: Optional[int] = None
    self_correction_attempts: int = Field(
        default=0,
        description="Number of LLM self-correction retries used (0 = first-pass success)"
    )


class RecomputeRequest(BaseModel):
    """Request payload for POST /api/recompute"""
    script_id: str
    python_code: str
    updated_parameters: Dict[str, float] = Field(
        ...,
        description="Dictionary of parameter names to updated float values from UI sliders"
    )


class RecomputeResponse(BaseModel):
    """Response payload for POST /api/recompute"""
    status: str
    script_id: str
    mesh_url: Optional[str] = None
    step_url: Optional[str] = None
    mesh_info: Optional[Dict[str, Any]] = None
    recomputation_time_ms: int
