"""
Unit tests for the LLM JSON response parser and AST validation guard (Week 3 deliverable).
"""
import pytest
from services.llm_service import LLMService, _robust_parse_json, _parse_response
from schemas import DualOutputPayload

def test_clean_json_parsing_with_fences():
    raw = """```json
    {
        "part_name": "Test Plate",
        "description": "Simple flat plate with mounting holes",
        "parameters": [
            {
                "name": "plate_width",
                "label": "Plate Width (mm)",
                "type": "number",
                "default": 100.0,
                "min": 50.0,
                "max": 200.0,
                "step": 1.0
            }
        ],
        "python_code": "PARAMS = {'plate_width': 100.0}\\nfrom build123d import *\\nwith BuildPart() as p:\\n    Box(PARAMS['plate_width'], 50, 5)"
    }
    ```"""
    payload = _parse_response(raw)
    assert isinstance(payload, DualOutputPayload)
    assert payload.part_name == "Test Plate"
    assert len(payload.parameters) == 1
    assert payload.parameters[0].name == "plate_width"

def test_non_strict_json_with_raw_newlines():
    # Contains literal unescaped newline in python_code string
    raw = """{
        "part_name": "Bracket",
        "description": "L Bracket",
        "parameters": [
            {"name": "thickness", "label": "Thickness", "type": "number", "default": 5.0, "min": 1.0, "max": 10.0, "step": 0.5}
        ],
        "python_code": "PARAMS = {'thickness': 5.0}
from build123d import *
with BuildPart() as p:
    Box(50, 50, PARAMS['thickness'])"
    }"""
    payload = _parse_response(raw)
    assert payload.part_name == "Bracket"
    assert "Box(50, 50, PARAMS['thickness'])" in payload.python_code

def test_regex_fallback_valid_ast():
    # JSON with syntax error in envelope but valid python_code block
    raw = """{
        "part_name": "Shaft Collar",
        "description": "Collar with set screw",
        "parameters": [
            {"name": "bore", "label": "Bore Diameter", "type": "number", "default": 8.0, "min": 3.0, "max": 25.0, "step": 1.0}
        ],
        "python_code": "PARAMS = {'bore': 8.0}\\nfrom build123d import *\\nwith BuildPart() as p:\\n    Cylinder(15, 10)",
        UNEXPECTED_TRAILING_GARBAGE
    """
    res = _robust_parse_json(raw)
    assert res["part_name"] == "Shaft Collar"
    assert "Cylinder(15, 10)" in res["python_code"]

def test_regex_fallback_rejects_corrupted_syntax():
    # JSON with broken python syntax that fails ast.parse
    raw = """{
        "part_name": "Broken Part",
        "description": "Corrupted Python",
        "parameters": [],
        "python_code": "def incomplete_func(x,: this is invalid python syntax !!!",
        BROKEN_JSON
    """
    with pytest.raises(ValueError) as excinfo:
        _robust_parse_json(raw)
    assert "Could not parse valid JSON or recover valid Python AST" in str(excinfo.value)
