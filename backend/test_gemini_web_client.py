"""
Unit Tests for Gemini Web Client & Fallback Integration
======================================================
Tests protocol payload structure, privacy flags, SAPISID hashing,
stream text parsing, and LLMService fallback integration.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from services.gemini_web_client import (
    resolve_model_specs,
    build_request_payload,
    build_request_headers,
    make_sapisidhash,
    clean_generated_text,
    extract_texts_from_line,
    parse_stream_response,
    GeminiWebError,
    is_configured,
)
from services.llm_service import LLMService


def test_resolve_model_specs():
    """Verify supported model names map to proper RPC mode IDs."""
    model, mode, think = resolve_model_specs("gemini-2.5-flash")
    assert mode == 1
    assert think == 4

    model, mode, think = resolve_model_specs("gemini-flash-lite")
    assert mode == 6


def test_payload_privacy_flags():
    """Verify that temporary chat flags are strictly enforced in RPC payload."""
    payload_str = build_request_payload(
        prompt="Create a cylinder",
        model_id=1,
        think_mode=4,
        enforce_temporary_chat=True,
    )
    assert "f.req=" in payload_str
    # Decode URL parameter
    import urllib.parse
    parsed = urllib.parse.parse_qs(payload_str)
    assert "f.req" in parsed
    outer = json.loads(parsed["f.req"][0])
    inner = json.loads(outer[1])

    # Assert temporary chat flags (privacy protection)
    assert inner[41] == [1], "inner[41] must be [1] for temporary chats"
    assert inner[45] == 1, "inner[45] must be 1 for temporary chats"
    assert inner[0][0] == "Create a cylinder"
    assert inner[79] == 1


def test_sapisid_hash_and_headers():
    """Verify SAPISIDHASH computation and masked header construction."""
    sapisid = "test_sapisid_secret"
    auth_header = make_sapisidhash(sapisid)
    assert auth_header.startswith("SAPISIDHASH ")
    assert "_" in auth_header

    headers = build_request_headers(
        cookie_str="SAPISID=test_sapisid_secret; __Secure-1PSID=xyz",
        sapisid=sapisid,
    )
    assert headers["Origin"] == "https://gemini.google.com"
    assert "SAPISIDHASH" in headers["Authorization"]
    assert "Cookie" in headers


def test_clean_generated_text():
    """Verify code execution markers and internal URLs are cleanly stripped."""
    raw = (
        "Here is the code:\n"
        "```python?code_reference&code_event_index=1\nprint('internal')\n```\n"
        "{\"part_name\": \"Bracket\", \"python_code\": \"Box(10, 10, 10)\", \"parameters\": []}\n"
        "http://googleusercontent.com/card_content/123\n"
    )
    cleaned = clean_generated_text(raw)
    assert "code_reference" not in cleaned
    assert "googleusercontent.com" not in cleaned
    assert "{\"part_name\": \"Bracket\"" in cleaned


def test_wrb_fr_parsing():
    """Verify parsing of wrb.fr streaming RPC format."""
    # Construct a valid wrb.fr line
    expected_content = "{\"part_name\": \"TestBox\", \"python_code\": \"Box(1, 2, 3)\", \"parameters\": []}"
    inner_struct = [None, None, None, None, [[None, [expected_content]]]]
    outer_struct = [["wrb.fr", None, json.dumps(inner_struct)]]
    line = json.dumps(outer_struct)

    extracted = extract_texts_from_line(line)
    assert len(extracted) == 1
    assert extracted[0] == expected_content


def test_parse_stream_response_error():
    """Verify BardErrorInfo detection triggers GeminiWebError."""
    rejection = ")]}'\n\n[[\"wrb.fr\", null, null, null, null, [\"BardErrorInfo [102]\"]]]"
    with pytest.raises(GeminiWebError) as exc_info:
        parse_stream_response(rejection)
    assert "102" in str(exc_info.value)


def test_llm_service_gemini_web_fallback():
    """Verify LLMService parses web response through robust parser."""
    mock_json_response = json.dumps({
        "part_name": "Web Parametric Cylinder",
        "description": "Generated via Gemini Web fallback",
        "parameters": [
            {"name": "radius", "label": "Radius (mm)", "type": "number", "default": 10.0, "min": 2.0, "max": 50.0, "step": 1.0}
        ],
        "python_code": (
            "PARAMS = {'radius': 10.0}\n"
            "from build123d import *\n"
            "with BuildPart() as part:\n"
            "    Cylinder(PARAMS['radius'], 30.0)\n"
            "export_stl(part.part, OUTPUT_STL)\n"
            "export_step(part.part, OUTPUT_STEP)\n"
        )
    })

    with patch("services.llm_service._call_gemini", side_effect=RuntimeError("API Quota 429")):
           with patch("services.gemini_web_client.is_configured", return_value=True), \
               patch("services.llm_service._call_gemini_web", return_value=mock_json_response):
            payload, model_used = LLMService._call_with_fallback(
                prompt="Cylinder with radius 10",
                system="Respond with JSON."
            )
            assert payload.part_name == "Web Parametric Cylinder"
            assert "gemini-web" in model_used
            assert len(payload.parameters) == 1
            assert "Cylinder" in payload.python_code
