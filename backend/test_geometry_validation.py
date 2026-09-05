"""
Unit tests for CAD Runner geometry validation and multi-body topology analysis (Week 8 deliverable).
"""
import pytest
import asyncio
from services.cad_runner import CADRunner

DISCONNECTED_BODIES_SCRIPT = """
PARAMS = {"spacing": 50.0}
from build123d import *

with BuildPart() as part:
    # Body 1 at origin
    Box(20, 20, 10)
    # Body 2 floating 50mm away with NO physical overlap
    with Locations((PARAMS["spacing"], 0, 0)):
        Box(20, 20, 10)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""

CONNECTED_MONOLITHIC_SCRIPT = """
PARAMS = {"overlap_length": 60.0}
from build123d import *

with BuildPart() as part:
    # Single monolithic body
    Box(PARAMS["overlap_length"], 20, 10)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""

STL_ONLY_SCRIPT = """
PARAMS = {"length": 20.0}
from build123d import *

with BuildPart() as part:
    Box(PARAMS["length"], 20, 10)

export_stl(part.part, OUTPUT_STL)
"""

@pytest.mark.asyncio
async def test_disconnected_bodies_detected():
    """Confirms that trimesh.graph.connected_components flags multiple disjoint bodies."""
    result = await CADRunner.execute_script_async(
        script_id="test_geo_disconnected",
        python_code=DISCONNECTED_BODIES_SCRIPT
    )
    assert result["status"] == "success"
    mesh_info = result["mesh_info"]
    assert mesh_info["body_count"] == 2
    assert mesh_info["is_valid"] is False
    assert any("disconnected bodies" in w for w in mesh_info["geometry_warnings"])


@pytest.mark.asyncio
async def test_multi_body_assembly_passes_mode_aware_validation():
    """A valid explicit assembly may contain multiple watertight bodies."""
    result = await CADRunner.execute_script_async(
        script_id="test_geo_assembly",
        python_code=DISCONNECTED_BODIES_SCRIPT,
        design_mode="assembly",
        component_names=["body_1", "body_2"],
    )
    assert result["status"] == "success"
    mesh_info = result["mesh_info"]
    assert mesh_info["validation_mode"] == "assembly"
    assert mesh_info["body_count"] == 2
    assert mesh_info["component_count"] == 2
    assert mesh_info["is_valid"] is True
    assert len(mesh_info["geometry_warnings"]) == 0


@pytest.mark.asyncio
async def test_connected_monolithic_solid_passes():
    """Confirms that a single fused watertight solid passes validation."""
    result = await CADRunner.execute_script_async(
        script_id="test_geo_connected",
        python_code=CONNECTED_MONOLITHIC_SCRIPT
    )
    assert result["status"] == "success"
    mesh_info = result["mesh_info"]
    assert mesh_info["body_count"] == 1
    assert mesh_info["is_watertight"] is True
    assert mesh_info["is_valid"] is True
    assert len(mesh_info["geometry_warnings"]) == 0


@pytest.mark.asyncio
async def test_missing_step_export_is_execution_failure():
    """A preview mesh without its production STEP export must not be accepted."""
    result = await CADRunner.execute_script_async(
        script_id="test_geo_missing_step",
        python_code=STL_ONLY_SCRIPT
    )
    assert result["status"] == "error"
    assert result["step_url"] is None
    assert "STEP" in result["stderr"]
