"""
Unit tests for Pydantic schemas and validation rules (Week 2 & 3 deliverables).
"""
import pytest
from pydantic import ValidationError
from schemas import CADParameter, DualOutputPayload, GenerateRequest, RecomputeRequest

def test_cad_parameter_valid_number():
    param = CADParameter(
        name="length",
        label="Length (mm)",
        type="number",
        default=50.0,
        min=10.0,
        max=100.0,
        step=0.5
    )
    assert param.name == "length"
    assert param.default == 50.0

def test_cad_parameter_valid_integer():
    param = CADParameter(
        name="bolt_count",
        label="Number of Bolts",
        type="integer",
        default=4.0,
        min=2.0,
        max=12.0,
        step=1.0
    )
    assert param.type == "integer"
    assert param.default == 4.0

def test_cad_parameter_invalid_range():
    with pytest.raises(ValidationError) as excinfo:
        CADParameter(
            name="width",
            label="Width (mm)",
            type="number",
            default=150.0,
            min=10.0,
            max=100.0,  # default > max
            step=1.0
        )
    assert "default (150.0) must be between min (10.0) and max (100.0)" in str(excinfo.value)

def test_cad_parameter_invalid_min_max():
    with pytest.raises(ValidationError) as excinfo:
        CADParameter(
            name="width",
            label="Width (mm)",
            type="number",
            default=50.0,
            min=100.0,  # min > max
            max=10.0,
            step=1.0
        )
    assert "min (100.0) must be <= max (10.0)" in str(excinfo.value)

def test_cad_parameter_invalid_integer_fraction():
    """Validates that non-whole numbers for integer types trigger validation errors."""
    with pytest.raises(ValidationError) as excinfo:
        CADParameter(
            name="rib_count",
            label="Rib Count",
            type="integer",
            default=3.5,  # Invalid for integer
            min=1.0,
            max=10.0,
            step=1.0
        )
    assert "type is 'integer' but default (3.5) is not a whole number" in str(excinfo.value)

def test_dual_output_payload_empty_parameters():
    with pytest.raises(ValidationError) as excinfo:
        DualOutputPayload(
            python_code="import build123d",
            parameters=[],  # min_length is 1
            part_name="Test Part",
            description="A test part"
        )
    assert "parameters" in str(excinfo.value)


def test_dual_output_rejects_assembly_description_in_single_solid_mode():
    with pytest.raises(ValidationError, match="describes an assembly"):
        DualOutputPayload(
            python_code='PARAMS = {"length": 20.0}\nfrom build123d import *',
            parameters=[
                {"name": "length", "label": "Length", "type": "number", "default": 20, "min": 10, "max": 50, "step": 1}
            ],
            part_name="Complete Mechanical Assembly",
            description="A complete mechanical assembly with separate modules.",
            design_mode="single_solid",
        )


def test_dual_output_rejects_single_solid_assertion_for_assembly_mode():
    with pytest.raises(ValidationError, match="must not assert exactly one solid"):
        DualOutputPayload(
            python_code=(
                'PARAMS = {"length": 20.0}\n'
                "from build123d import *\n"
                "base_plate = object()\n"
                "cover_plate = object()\n"
                "solids = part.part.solids()\n"
                "assert len(solids) == 1\n"
            ),
            parameters=[
                {"name": "length", "label": "Length", "type": "number", "default": 20, "min": 10, "max": 50, "step": 1}
            ],
            part_name="Fixture Assembly",
            description="A multi-part assembly with separate plates.",
            design_mode="assembly",
            components=["base_plate", "cover_plate"],
        )


def test_generate_request_rejects_oversized_prompt():
    with pytest.raises(ValidationError):
        GenerateRequest(prompt="x" * 10_001)


def test_recompute_rejects_unknown_parameter_name():
    with pytest.raises(ValidationError, match="Unknown parameter"):
        RecomputeRequest(
            script_id="part_example",
            python_code='PARAMS = {"length": 20.0}',
            updated_parameters={"width": 10.0},
        )


def test_recompute_rejects_oversized_script():
    with pytest.raises(ValidationError):
        RecomputeRequest(
            script_id="part_example",
            python_code="PARAMS = {}\n" + ("#" * 500_001),
            updated_parameters={},
        )


def test_recompute_enforces_declared_parameter_bounds_and_integer_type():
    params = [
        {"name": "length", "label": "Length", "type": "number", "default": 20, "min": 10, "max": 50, "step": 1},
        {"name": "holes", "label": "Holes", "type": "integer", "default": 4, "min": 2, "max": 8, "step": 1},
    ]
    base = {
        "script_id": "part_example",
        "python_code": 'PARAMS = {"length": 20.0, "holes": 4}',
        "parameters": params,
    }
    with pytest.raises(ValidationError, match="outside"):
        RecomputeRequest(**base, updated_parameters={"length": 100.0})
    with pytest.raises(ValidationError, match="whole number"):
        RecomputeRequest(**base, updated_parameters={"holes": 3.5})
