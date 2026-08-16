"""
Unit tests for Pydantic schemas and validation rules (Week 2 & 3 deliverables).
"""
import pytest
from pydantic import ValidationError
from schemas import CADParameter, DualOutputPayload, GenerateRequest

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
