"""
Pydantic Schemas for the AI-Driven Parametric CAD Workbench.

Defines the Dual-Output API contract:
  - CADParameter: A single configurable parameter (slider) extracted by the LLM.
  - DualOutputPayload: The full LLM response containing executable code + parameter schema.
  - GenerateRequest / GenerateResponse: /api/generate endpoint contracts.
  - RecomputeRequest / RecomputeResponse: /api/recompute endpoint contracts.
  - ModifyRequest / ModifyResponse: /api/modify (Chat-to-Modify) endpoint contracts.
"""
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Core Parameter Schema
# ---------------------------------------------------------------------------

class CADParameter(BaseModel):
    """
    Represents a single configurable design variable exposed as a UI slider.
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
    unit: Optional[str] = Field(
        default=None,
        description="Physical unit (e.g. 'mm', 'deg', 'count')"
    )
    default: float = Field(..., description="Default starting value")
    min: float = Field(..., description="Minimum allowed value")
    max: float = Field(..., description="Maximum allowed value")
    step: float = Field(default=1.0, description="Slider step increment")

    @model_validator(mode='after')
    def validate_range(self) -> 'CADParameter':
        """Ensures min <= default <= max, step > 0, and integer consistency."""
        if self.min > self.max:
            raise ValueError(f"Parameter '{self.name}': min ({self.min}) must be <= max ({self.max})")
        if not (self.min <= self.default <= self.max):
            raise ValueError(
                f"Parameter '{self.name}': default ({self.default}) must be between "
                f"min ({self.min}) and max ({self.max})"
            )
        if self.step <= 0:
            raise ValueError(f"Parameter '{self.name}': step ({self.step}) must be > 0")

        # Integer consistency check
        if self.type == "integer":
            for field_name, val in [("default", self.default), ("min", self.min), ("max", self.max), ("step", self.step)]:
                if not float(val).is_integer():
                    raise ValueError(
                        f"Parameter '{self.name}': type is 'integer' but {field_name} ({val}) is not a whole number"
                    )
        return self


# ---------------------------------------------------------------------------
# Dual-Output Payload (LLM Response Schema)
# ---------------------------------------------------------------------------

class DualOutputPayload(BaseModel):
    """
    The structured JSON payload the LLM must produce.
    Contains BOTH the executable Python CAD script AND the parameter schema.
    """
    python_code: str = Field(
        ...,
        description=(
            "Complete, executable Python script using the build123d library. "
            "MUST begin with a PARAMS = {...} dictionary block. "
            "MUST export the output to OUTPUT_STL and OUTPUT_STEP variables provided by the runtime."
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
    model_used: Optional[str] = Field(
        default=None,
        description="Which LLM model (tier) served the request"
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
    recomputation_time_ms: Optional[int] = None   # Consistent Optional with GenerateResponse


# ---------------------------------------------------------------------------
# Chat-to-Modify Request / Response Models
# ---------------------------------------------------------------------------

class ModifyRequest(BaseModel):
    """Request payload for POST /api/modify (Chat-to-Modify)"""
    script_id: str = Field(
        ...,
        description="ID of the existing generated script to modify"
    )
    python_code: str = Field(
        ...,
        description="The current build123d Python script to be modified"
    )
    part_name: str = Field(
        ...,
        description="Current part name for context"
    )
    modification_prompt: str = Field(
        ...,
        description="Natural language description of the desired change",
        min_length=3
    )
    parameters: List[CADParameter] = Field(
        default=[],
        description="Existing parameter definitions for context preservation"
    )


class ModifyResponse(BaseModel):
    """Response payload for POST /api/modify (Chat-to-Modify)"""
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
    model_used: Optional[str] = None
    modification_summary: Optional[str] = Field(
        default=None,
        description="The modification prompt that produced this version"
    )
