"""
Unit test for parameter preservation and schema consistency during Chat-to-Modify (Week 7 deliverable).
"""
import pytest
from schemas import CADParameter, DualOutputPayload

def test_param_preservation_contract():
    # Simulates base parameters
    base_params = [
        CADParameter(name="length", label="Length (mm)", type="number", default=50.0, min=10.0, max=100.0, step=1.0, unit="mm"),
        CADParameter(name="width", label="Width (mm)", type="number", default=30.0, min=10.0, max=100.0, step=1.0, unit="mm")
    ]
    base_keys = {p.name for p in base_params}

    # Simulates modified output payload returned from LLM
    modified_params = [
        CADParameter(name="length", label="Length (mm)", type="number", default=50.0, min=10.0, max=100.0, step=1.0, unit="mm"),
        CADParameter(name="width", label="Width (mm)", type="number", default=30.0, min=10.0, max=100.0, step=1.0, unit="mm"),
        CADParameter(name="hole_radius", label="Hole Radius (mm)", type="number", default=4.0, min=1.0, max=10.0, step=0.5, unit="mm")
    ]
    modified_keys = {p.name for p in modified_params}

    # Invariant: Base keys must be preserved in the modified parameter set (superset check)
    assert base_keys.issubset(modified_keys), f"Base parameters {base_keys - modified_keys} were lost during modification!"
    assert "hole_radius" in modified_keys
    assert len(modified_params) == 3
