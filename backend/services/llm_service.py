"""
LLM Service — Gemini 1.5 Dual-Output CAD Code Generator
=========================================================
Responsibilities:
  1. Builds a structured system prompt instructing Gemini to output
     both executable Python CAD code AND a JSON parameter schema.
  2. Calls Gemini API with JSON-mode enforcement.
  3. Parses and validates the response into a DualOutputPayload.
  4. Implements a self-correction loop (up to 3 retries) when
     generated code fails to execute in the CAD runner.
"""

import os
import json
import logging
from typing import Optional
from google import genai
from google.genai import types
from pydantic import ValidationError

from config import GEMINI_API_KEY
from schemas import DualOutputPayload, CADParameter

logger = logging.getLogger("cad_workbench.llm_service")

# ---------------------------------------------------------------------------
# Gemini Client Initialization
# ---------------------------------------------------------------------------

def _get_client() -> genai.Client:
    api_key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. "
            "Please add it to your .env file or environment variables."
        )
    return genai.Client(api_key=api_key)


# ---------------------------------------------------------------------------
# System Prompt Templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert CAD engineer and Python programmer specializing in parametric 3D solid modeling.

Your task is to generate a complete Python script for creating a 3D mechanical part using the trimesh library, along with a structured parameter schema.

## Output Format
You MUST respond with a single, valid JSON object (no markdown, no code fences) matching this exact schema:

{
  "python_code": "<complete Python script as a string>",
  "parameters": [
    {
      "name": "<variable_name>",
      "label": "<Human Readable Label (unit)>",
      "type": "number",
      "default": <number>,
      "min": <number>,
      "max": <number>,
      "step": <number>
    }
  ],
  "part_name": "<Short Part Name>",
  "description": "<One sentence describing the part>"
}

## Python Script Rules
1. The script MUST start with a PARAMS dictionary block at the top:
   ```
   PARAMS = {
       "param_name": default_value,
       ...
   }
   ```
2. Use ONLY the trimesh library for geometry (e.g. trimesh.creation.box, trimesh.creation.cylinder, trimesh.creation.cone).
3. The script MUST write the final mesh to the variable OUTPUT_STL (provided by runtime):
   ```
   mesh.export(OUTPUT_STL)
   ```
4. Do NOT use FreeCAD, cadquery, or any other CAD library - ONLY trimesh.
5. All dimensions are in millimeters.
6. Use boolean operations via trimesh.boolean for cuts/holes if needed.
7. Always compute vertex normals after boolean ops: mesh.fix_normals()

## Parameter Schema Rules
1. Every key in PARAMS must have a corresponding entry in the parameters array.
2. Names must match exactly between PARAMS dict and parameter "name" fields.
3. Provide sensible min/max/step values for each parameter.
4. Include 2-6 parameters per part.

## Example for "a 30mm cube":
{
  "python_code": "PARAMS = {\\n    \\"side_length\\": 30.0\\n}\\n\\nimport trimesh\\n\\nside = PARAMS[\\"side_length\\"]\\nmesh = trimesh.creation.box(extents=[side, side, side])\\nmesh.export(OUTPUT_STL)\\nprint(f\\"Cube {side}x{side}x{side} mm exported\\")\\n",
  "parameters": [
    {
      "name": "side_length",
      "label": "Side Length (mm)",
      "type": "number",
      "default": 30.0,
      "min": 5.0,
      "max": 200.0,
      "step": 1.0
    }
  ],
  "part_name": "Cube",
  "description": "A simple parametric cube with configurable side length."
}
"""

CORRECTION_PROMPT_TEMPLATE = """The Python CAD script you generated previously failed to execute.

## Original User Request
{user_prompt}

## Failed Script
```python
{failed_code}
```

## Error Traceback
```
{error_traceback}
```

## Your Task
Fix the script and return a corrected, complete JSON response (same schema as before).
Common fixes:
- Ensure PARAMS dict is at the top with correct variable names.
- Check trimesh API usage (use trimesh.creation.box, .cylinder, .cone).
- Fix any math errors (zero division, negative dimensions, etc.).
- Ensure mesh.export(OUTPUT_STL) is called at the end.
- Do NOT use boolean operations if they cause errors — use simpler geometry instead.

Return ONLY the corrected JSON object, no markdown, no explanation.
"""


# ---------------------------------------------------------------------------
# LLM Service Class
# ---------------------------------------------------------------------------

class LLMService:
    """
    Orchestrates Gemini 1.5 API calls for dual-output parametric CAD generation.
    """

    MODEL_ID = "gemini-1.5-flash"
    MAX_RETRIES = 3

    @classmethod
    def _call_gemini(cls, prompt: str, system: str = SYSTEM_PROMPT) -> str:
        """
        Calls Gemini with JSON-mode enforcement.
        Returns raw JSON string.
        """
        client = _get_client()
        response = client.models.generate_content(
            model=cls.MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                temperature=0.2,          # Low temperature for deterministic code
                max_output_tokens=4096,
            )
        )
        return response.text

    @classmethod
    def generate_dual_output(cls, user_prompt: str) -> DualOutputPayload:
        """
        Calls Gemini with the user's natural language prompt.
        Parses and validates the response into a DualOutputPayload.
        Raises ValueError if all retries fail.
        """
        raw_json = cls._call_gemini(user_prompt)
        logger.info(f"[LLM] Raw response received ({len(raw_json)} chars)")
        return cls._parse_response(raw_json)

    @classmethod
    def correct_code(
        cls,
        user_prompt: str,
        failed_code: str,
        error_traceback: str
    ) -> DualOutputPayload:
        """
        Sends the broken script + traceback back to Gemini for self-correction.
        Returns a corrected DualOutputPayload.
        """
        correction_prompt = CORRECTION_PROMPT_TEMPLATE.format(
            user_prompt=user_prompt,
            failed_code=failed_code,
            error_traceback=error_traceback
        )
        logger.info(f"[LLM] Sending correction prompt for traceback: {error_traceback[:100]}...")
        raw_json = cls._call_gemini(correction_prompt)
        return cls._parse_response(raw_json)

    @staticmethod
    def _parse_response(raw_json: str) -> DualOutputPayload:
        """
        Parses raw JSON string from Gemini into a validated DualOutputPayload.
        Handles common response formatting issues.
        """
        # Strip accidental markdown fences if present despite JSON mode
        text = raw_json.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(
                line for line in lines
                if not line.startswith("```")
            ).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Gemini returned invalid JSON: {e}\nRaw: {raw_json[:300]}")

        try:
            payload = DualOutputPayload(**data)
        except (ValidationError, TypeError) as e:
            raise ValueError(f"Response failed schema validation: {e}")

        return payload
