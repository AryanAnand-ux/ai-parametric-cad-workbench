"""
Pydantic Schemas for the AI-Driven Parametric CAD Workbench.

Defines the Dual-Output API contract:
  - CADParameter: A single configurable parameter (slider) extracted by the LLM.
  - DualOutputPayload: The full LLM response containing executable code + parameter schema.
  - GenerateRequest / GenerateResponse: /api/generate endpoint contracts.
  - RecomputeRequest / RecomputeResponse: /api/recompute endpoint contracts.
  - ModifyRequest / ModifyResponse: /api/modify (Chat-to-Modify) endpoint contracts.
"""
import ast
import math
import re
from typing import List, Literal, Optional, Dict, Any
from pydantic import Field, BaseModel, model_validator


# ---------------------------------------------------------------------------
# Core Parameter Schema
# ---------------------------------------------------------------------------

class CADParameter(BaseModel):
    """
    Represents a single configurable design variable exposed as a UI slider.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z_][A-Za-z0-9_]*$",
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
        min_length=1,
        max_length=500_000,
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
        min_length=1,
        max_length=120,
        description="Short descriptive name for the generated part (e.g. 'Mounting Bracket')"
    )
    description: str = Field(
        ...,
        description="One-sentence description of the generated part and its key design features"
    )
    design_mode: Literal["single_solid", "assembly"] = Field(
        default="single_solid",
        description=(
            "single_solid: exactly one watertight solid required. "
            "assembly: multiple named components allowed, each validated separately."
        )
    )
    components: Optional[List[str]] = Field(
        default=None,
        description=(
            "For assembly mode: list of component names that must exist in the script "
            "(e.g. ['chassis', 'wheel_fl', 'motor_fl']). "
            "Each component must be assigned to a variable with this exact name."
        )
    )

    @model_validator(mode="after")
    def validate_design_mode_consistency(self) -> "DualOutputPayload":
        """Keep assembly metadata consistent with the generated script contract."""
        components = self.components or []
        text = f"{self.part_name} {self.description}".lower()
        says_assembly = any(
            phrase in text
            for phrase in (
                "mechanical assembly",
                "complete assembly",
                "multi-part assembly",
                "multiple components",
            )
        )
        single_solid_assert = re.search(
            r"assert\s+len\s*\(\s*solids\s*\)\s*==\s*1|"
            r"assert\s+len\s*\(\s*part\.part\.solids\s*\(\s*\)\s*\)\s*==\s*1",
            self.python_code,
        )

        if self.design_mode == "single_solid":
            if components:
                raise ValueError("single_solid payloads must not declare assembly components")
            if says_assembly:
                raise ValueError("description/part_name describes an assembly but design_mode is single_solid")

        if self.design_mode == "assembly":
            if not components:
                raise ValueError("assembly payloads must declare at least one component")
            if len(set(components)) != len(components):
                raise ValueError("assembly components must be unique")
            invalid_names = [name for name in components if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name)]
            if invalid_names:
                raise ValueError(f"assembly components must be valid Python identifiers: {', '.join(invalid_names)}")
            try:
                tree = ast.parse(self.python_code)
            except SyntaxError as exc:
                raise ValueError(f"python_code syntax error: {exc}") from exc
            assigned_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    assigned_names.update(
                        target.id for target in node.targets if isinstance(target, ast.Name)
                    )
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    assigned_names.add(node.target.id)
            missing_components = sorted(set(components) - assigned_names)
            if missing_components:
                raise ValueError(
                    "assembly components must be assigned in python_code: "
                    + ", ".join(missing_components)
                )
            if single_solid_assert:
                raise ValueError("assembly payloads must not assert exactly one solid")

        return self


# ---------------------------------------------------------------------------
# API Request / Response Models
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    """Request payload for POST /api/generate"""
    prompt: str = Field(
        ...,
        description="Natural language description of the 3D part to generate",
        min_length=5,
        max_length=2000,
    )


class GenerateResponse(BaseModel):
    """Response payload for POST /api/generate"""
    status: str
    script_id: str
    part_name: str
    description: str
    python_code: str
    parameters: List[CADParameter]
    design_mode: str = Field(default="single_solid")
    components: Optional[List[str]] = None
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
    script_id: str = Field(..., min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    python_code: str = Field(..., min_length=1, max_length=500_000)
    updated_parameters: Dict[str, float] = Field(
        ...,
        max_length=64,
        description="Dictionary of parameter names to updated float values from UI sliders"
    )
    parameters: List[CADParameter] = Field(default_factory=list, max_length=64)
    design_mode: Literal["single_solid", "assembly"] = Field(default="single_solid")
    components: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_updated_parameters(self) -> "RecomputeRequest":
        try:
            tree = ast.parse(self.python_code)
            params_node = next(
                node for node in tree.body
                if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "PARAMS" for target in node.targets)
            )
            params = ast.literal_eval(params_node.value)
        except (StopIteration, SyntaxError, ValueError, TypeError) as exc:
            raise ValueError("python_code must contain a literal PARAMS dictionary") from exc

        if not isinstance(params, dict):
            raise ValueError("PARAMS must be a dictionary")
        unknown = set(self.updated_parameters) - set(params)
        if unknown:
            raise ValueError(f"Unknown parameter(s): {', '.join(sorted(unknown))}")
        if any(not math.isfinite(value) for value in self.updated_parameters.values()):
            raise ValueError("Updated parameters must be finite numbers")
        definitions = {parameter.name: parameter for parameter in self.parameters}
        for name, value in self.updated_parameters.items():
            definition = definitions.get(name)
            if definition is None:
                continue
            if not definition.min <= value <= definition.max:
                raise ValueError(f"Parameter '{name}' value is outside its declared range")
            if definition.type == "integer" and not float(value).is_integer():
                raise ValueError(f"Parameter '{name}' must be a whole number")
        return self


class RecomputeResponse(BaseModel):
    """Response payload for POST /api/recompute"""
    status: str
    script_id: str
    mesh_url: Optional[str] = None
    step_url: Optional[str] = None
    mesh_info: Optional[Dict[str, Any]] = None
    recomputation_time_ms: Optional[int] = None   # Consistent Optional with GenerateResponse
    design_mode: str = Field(default="single_solid")
    components: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# Chat-to-Modify Request / Response Models
# ---------------------------------------------------------------------------

class ModifyRequest(BaseModel):
    """Request payload for POST /api/modify (Chat-to-Modify)"""
    script_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="ID of the existing generated script to modify"
    )
    python_code: str = Field(
        ...,
        min_length=1,
        max_length=500_000,
        description="The current build123d Python script to be modified"
    )
    part_name: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Current part name for context"
    )
    modification_prompt: str = Field(
        ...,
        description="Natural language description of the desired change",
        min_length=3,
        max_length=2000,
    )
    parameters: List[CADParameter] = Field(
        default_factory=list,
        description="Existing parameter definitions for context preservation"
    )
    design_mode: Literal["single_solid", "assembly"] = Field(default="single_solid")
    components: Optional[List[str]] = None


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
    design_mode: str = Field(default="single_solid")
    components: Optional[List[str]] = None
    modification_summary: Optional[str] = Field(
        default=None,
        description="The modification prompt that produced this version"
    )
