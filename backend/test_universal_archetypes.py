"""
Tests for Universal CAD Archetypes:
1. Archetype detection in LLM service
2. Semantic RAG retrieval across the 121-example corpus
3. Syntax and AST sandbox validation of all 20 universal archetypes
4. Kernel execution and solid geometry generation for selected archetypes
"""

import ast
import pytest
from services.llm_service import _detect_cad_archetype
from services.rag_service import RAGService
from services.cad_runner import validate_script_safety
from rag_corpus.examples_universal import EXAMPLES as UNIV_EXAMPLES


def test_archetype_detection():
    """Verify that intent classifier recognizes key archetypes."""
    assert "ROTATIONAL" in _detect_cad_archetype("Design a stepped motor shaft with bearing seats")
    assert "ROTATIONAL" in _detect_cad_archetype("Make a double-groove V-belt pulley")
    assert "ENCLOSURE" in _detect_cad_archetype("Electronics enclosure box with corner screw bosses")
    assert "RADIAL / GEAR" in _detect_cad_archetype("24 tooth spur gear with module 2.5 and keyed bore")
    assert "SWEPT TUBING" in _detect_cad_archetype("90 degree flanged pipe elbow")
    assert "LOFTED TRANSITION" in _detect_cad_archetype("Square to round ventilation duct transition")
    assert "STRUCTURAL BRACKET" in _detect_cad_archetype("Heavy duty 90 degree gusseted angle bracket")
    assert "CONSUMER / ERGONOMIC" in _detect_cad_archetype("Desktop ergonomic phone stand with cable slot")
    assert "CONSUMER / ERGONOMIC" in _detect_cad_archetype("Ceramic coffee mug with handle")
    assert "MECHANICAL ASSEMBLY" in _detect_cad_archetype("ISO metric hex bolt and nut assembly")


def test_rag_retrieval_universal_coverage():
    """Verify that semantic RAG retrieves appropriate universal archetypes."""
    # Test queries
    test_cases = [
        ("stepped drive shaft with keyway and circlip", ["shaft", "stepped", "lathe"]),
        ("electronics enclosure box with standoffs", ["enclosure", "box", "case"]),
        ("involute spur gear with hub and keyed bore", ["gear", "spur", "teeth"]),
        ("heavy duty 90 degree angle bracket with stiffener gusset", ["bracket", "gusset", "angle"]),
        ("square to round lofted duct adapter", ["duct", "loft", "transition"]),
        ("ceramic coffee mug with curved handle", ["mug", "cup", "handle"]),
    ]

    for query, expected_keywords in test_cases:
        results = RAGService.retrieve(query, k=3, min_similarity=0.10)
        assert len(results) > 0, f"RAG returned no results for query: {query}"
        combined_text = (results[0]["description"] + " " + results[0]["tags"]).lower()
        matched = any(kw in combined_text for kw in expected_keywords)
        assert matched, f"Top match '{results[0]['description']}' did not match keywords {expected_keywords} for query '{query}'"


def test_all_20_universal_examples_syntax_and_security():
    """Verify that all 20 universal example scripts pass syntax and AST security."""
    assert len(UNIV_EXAMPLES) == 20, f"Expected 20 universal examples, got {len(UNIV_EXAMPLES)}"

    for ex in UNIV_EXAMPLES:
        code = ex["code"]
        # 1. Valid Python syntax
        tree = ast.parse(code)
        assert tree is not None, f"Failed to parse AST for {ex['id']}"

        # 2. Contains PARAMS dictionary
        assert "PARAMS = {" in code, f"{ex['id']} missing PARAMS block"

        # 3. Contains BuildPart context
        assert "with BuildPart() as part:" in code, f"{ex['id']} missing BuildPart context"

        # 4. AST security sanitizer check
        is_safe, reason = validate_script_safety(code)
        assert is_safe, f"{ex['id']} failed AST security check: {reason}"


def test_execute_stepped_shaft_geometry(tmp_path):
    """Executes universal_stepped_shaft and verifies 1 monolithic solid."""
    ex = next(x for x in UNIV_EXAMPLES if x["id"] == "universal_stepped_shaft")
    stl_path = str(tmp_path / "shaft.stl")
    step_path = str(tmp_path / "shaft.step")

    exec_globals = {
        "OUTPUT_STL": stl_path,
        "OUTPUT_STEP": step_path,
    }
    exec(ex["code"], exec_globals)

    part = exec_globals["part"]
    assert part.part is not None
    assert len(part.part.solids()) == 1
    bb = part.part.bounding_box()
    assert bb.size.Z > 100.0  # 25 + 35 + 50 = 110mm


def test_execute_electronics_enclosure_geometry(tmp_path):
    """Executes universal_electronics_enclosure and verifies geometry."""
    ex = next(x for x in UNIV_EXAMPLES if x["id"] == "universal_electronics_enclosure")
    stl_path = str(tmp_path / "box.stl")
    step_path = str(tmp_path / "box.step")

    exec_globals = {
        "OUTPUT_STL": stl_path,
        "OUTPUT_STEP": step_path,
    }
    exec(ex["code"], exec_globals)

    part = exec_globals["part"]
    assert part.part is not None
    assert len(part.part.solids()) == 1
    bb = part.part.bounding_box()
    assert abs(bb.size.X - 120.0) < 0.5
    assert abs(bb.size.Y - 80.0) < 0.5
