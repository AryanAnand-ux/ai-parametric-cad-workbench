"""
Unit tests for cad_verifier.py — Closed-Loop Multi-View Visual Intent Verification.
Hermetic tests with monkeypatched LLM responses.
"""

from unittest.mock import MagicMock, patch
import trimesh

from services.cad_verifier import CADVerifier, VisualVerificationAnalysis, VisualCheckItem


def test_cad_verifier_mock_direct():
    box = trimesh.creation.box((10.0, 10.0, 10.0))
    mock_resp = {
        "intent_score": 0.5,
        "passed_checks": 1,
        "total_checks": 2,
        "is_verified": False,
        "part_summary": "Solid box without hole",
        "checks": [
            {"criterion": "Box dimensions 10x10x10", "passed": True, "explanation": "Matches box size"},
            {"criterion": "Central hole", "passed": False, "explanation": "No hole cutout visible in Top view"},
        ],
        "corrective_feedback": "Add central through-hole using Hole()",
    }
    
    result = CADVerifier.verify_mesh("A box with a center hole", box, mock_response=mock_resp)
    assert result["intent_score"] == 0.5
    assert result["passed_checks"] == 1
    assert result["total_checks"] == 2
    assert not result["is_verified"]
    assert result["corrective_feedback"] == "Add central through-hole using Hole()"


def test_cad_verifier_gemini_parsing():
    analysis = VisualVerificationAnalysis(
        part_summary="Precision L-bracket with dual mounting holes",
        checks=[
            VisualCheckItem(criterion="L-bracket arms 50mm", passed=True, explanation="Two perpendicular arms visible"),
            VisualCheckItem(criterion="Mounting holes", passed=True, explanation="Two circular holes visible on face"),
        ],
        corrective_feedback=None,
    )
    
    mock_gen_response = MagicMock()
    mock_gen_response.text = analysis.model_dump_json()

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_gen_response

    box = trimesh.creation.box((20.0, 20.0, 5.0))
    
    with patch("config.GEMINI_API_KEY", "test_key"), \
         patch("google.genai.Client", return_value=mock_client):
        result = CADVerifier.verify_mesh("L-bracket with mounting holes", box)
        
        assert result["intent_score"] == 1.0
        assert result["passed_checks"] == 2
        assert result["total_checks"] == 2
        assert result["is_verified"] is True
        assert result["corrective_feedback"] is None


def test_cad_verifier_no_api_keys():
    box = trimesh.creation.box((10.0, 10.0, 10.0))
    with patch("config.GEMINI_API_KEY", None), patch("config.GROQ_API_KEY", None):
        result = CADVerifier.verify_mesh("A test bracket", box)
        assert result["is_verified"] is True
        assert result["intent_score"] == 1.0
