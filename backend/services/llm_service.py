"""
LLM Service — 3-Tier Dual-Model Strategy
==========================================
Tier 1 (Primary)   : Gemini 2.0 Flash  (google-genai, native JSON mode, free tier)
Tier 2 (Secondary) : Gemini 2.5 Flash  (google-genai, separate quota pool)
Tier 3 (Fallback)  : Groq Llama-3.3-70B (10x faster inference, always-on free tier)

Flow:
  1. Try Gemini 2.0 Flash first (best quality).
  2. If Gemini 2.0 fails → try Gemini 2.5 Flash (same key, different model quota).
  3. If both Gemini fail → switch to Groq Llama-3.3-70B (always available).
  4. Self-correction loop (up to 3 retries) runs on whichever model last succeeded.

NOTE: Tiers 1 & 2 share the same GEMINI_API_KEY. "Separate quota" refers to
per-model rate limits, not per-key limits. If the account-level daily cap is hit,
both Gemini tiers will fail and Groq will handle all requests.
"""

import os
import json
import logging
from typing import Tuple

from pydantic import ValidationError

from config import GEMINI_API_KEY, GROQ_API_KEY
from schemas import DualOutputPayload

logger = logging.getLogger("cad_workbench.llm_service")


# ---------------------------------------------------------------------------
# System Prompts
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
1. The script MUST start with a PARAMS dictionary block at the very top:
   PARAMS = {
       "param_name": default_value,
       ...
   }
2. Use ONLY the trimesh library for geometry. Allowed functions:
   - trimesh.creation.box(extents=[l, w, h])
   - trimesh.creation.cylinder(radius=r, height=h, sections=32)
   - trimesh.creation.cone(radius=r, height=h, sections=32)
   - trimesh.creation.annulus(r_min, r_max, height)   # hollow cylinder — positional args only
3. ALWAYS include 'import trimesh' at the top of the script (after PARAMS block).
4. The script MUST write the final mesh to OUTPUT_STL (injected by runtime — do NOT redefine it):
   mesh.export(OUTPUT_STL)
5. Do NOT use FreeCAD, cadquery, or any other library — ONLY trimesh.
6. All dimensions are in millimeters.
7. To combine multiple parts: use trimesh.util.concatenate([mesh1, mesh2])
   NOTE: concatenate merges geometry visually but does NOT compute boolean union.
   Avoid overlapping geometry — place parts side by side instead.
8. Keep geometry simple and watertight. Prefer primitives over boolean operations.
   If you must subtract geometry, use trimesh.boolean.difference([mesh_a, mesh_b])
   but only for simple non-overlapping cases.

## Parameter Schema Rules
1. Every key in PARAMS must have a matching entry in the parameters array.
2. Names must match exactly (case-sensitive) between PARAMS and the parameters list.
3. Include 2–5 meaningful parameters per part.
4. Ensure min <= default <= max for every parameter.
5. Provide sensible step values (e.g. 1.0 for whole mm, 0.5 for half mm).

## Example for "a 30mm cube":
{
  "python_code": "PARAMS = {\\n    \\"side_length\\": 30.0\\n}\\n\\nimport trimesh\\n\\nside = PARAMS[\\"side_length\\"]\\nmesh = trimesh.creation.box(extents=[side, side, side])\\nmesh.export(OUTPUT_STL)\\n",
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

## Error Traceback (most recent call last)
```
{error_traceback}
```

## Fix Instructions
Return the corrected complete JSON object (same schema, no markdown, no code fences).

Common causes and fixes:
- Missing 'import trimesh' — ensure it appears after the PARAMS block.
- OUTPUT_STL is a string path injected at runtime — do NOT redefine or override it.
- PARAMS dict must be at the very top of the script before any other code.
- Only use trimesh.creation.* functions — no FreeCAD, no cadquery.
- Use positional args for annulus: trimesh.creation.annulus(inner_r, outer_r, height).
- Avoid trimesh.boolean operations if they fail — use simple primitives instead.
- Ensure mesh.export(OUTPUT_STL) is the very last line.
- Fix any math errors (zero division, negative dimensions, sqrt of negative).

Return ONLY the corrected JSON object.
"""


# ---------------------------------------------------------------------------
# Response Parser (shared by all model tiers)
# ---------------------------------------------------------------------------

def _parse_response(raw_text: str) -> DualOutputPayload:
    """
    Parses raw LLM text into a validated DualOutputPayload.
    Handles accidental markdown fences gracefully.
    """
    text = raw_text.strip()

    # Strip markdown fences if present despite JSON mode
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}\nRaw snippet: {raw_text[:300]}")

    try:
        return DualOutputPayload(**data)
    except (ValidationError, TypeError) as e:
        raise ValueError(f"Response failed schema validation: {e}")


# ---------------------------------------------------------------------------
# Gemini Client (Tier 1: gemini-2.0-flash, Tier 2: gemini-2.5-flash)
# ---------------------------------------------------------------------------

def _call_gemini(prompt: str, system: str = SYSTEM_PROMPT, model: str = "gemini-2.0-flash") -> str:
    """Calls a Gemini model with native JSON mode enforcement."""
    from google import genai
    from google.genai import types

    api_key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not configured.")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            temperature=0.2,
            max_output_tokens=8192,
        )
    )
    return response.text


# ---------------------------------------------------------------------------
# Groq Client (Tier 3: llama-3.3-70b-versatile)
# ---------------------------------------------------------------------------

def _call_groq(prompt: str, system: str = SYSTEM_PROMPT) -> str:
    """
    Calls Groq Llama-3.3-70B as a high-speed tertiary fallback.
    Uses JSON mode enforcement via response_format.
    NOTE: Groq requires the word "json" to appear in the system/user message
    when using response_format={"type": "json_object"} — SYSTEM_PROMPT satisfies this.
    """
    from groq import Groq

    api_key = GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not configured.")

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=8192,   # Match Gemini tier to prevent JSON truncation
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Main LLM Service Class
# ---------------------------------------------------------------------------

class LLMService:
    """
    3-Tier LLM orchestrator:
      Tier 1: Gemini 2.0 Flash (primary)
      Tier 2: Gemini 2.5 Flash (secondary, separate model quota)
      Tier 3: Groq Llama-3.3-70B (always-on fallback)
    """

    MAX_RETRIES = 3

    @classmethod
    def _call_with_fallback(cls, prompt: str, system: str = SYSTEM_PROMPT) -> Tuple[str, str]:
        """
        3-tier fallback chain. Returns (raw_json_string, model_name_used).
        """
        errors = []

        # --- Tier 1: Gemini 2.0 Flash ---
        try:
            logger.info("[LLM] Calling Gemini 2.0 Flash (Tier 1)...")
            raw = _call_gemini(prompt, system, model="gemini-2.0-flash")
            logger.info(f"[LLM] Gemini 2.0 Flash responded ({len(raw)} chars)")
            return raw, "gemini-2.0-flash"
        except Exception as e:
            errors.append(f"gemini-2.0-flash: {e}")
            logger.warning(f"[LLM] Tier 1 failed: {e}")

        # --- Tier 2: Gemini 2.5 Flash ---
        try:
            logger.info("[LLM] Calling Gemini 2.5 Flash (Tier 2)...")
            raw = _call_gemini(prompt, system, model="gemini-2.5-flash")
            logger.info(f"[LLM] Gemini 2.5 Flash responded ({len(raw)} chars)")
            return raw, "gemini-2.5-flash"
        except Exception as e:
            errors.append(f"gemini-2.5-flash: {e}")
            logger.warning(f"[LLM] Tier 2 failed: {e}")

        # --- Tier 3: Groq Llama-3.3-70B ---
        try:
            logger.info("[LLM] Calling Groq Llama-3.3-70B (Tier 3)...")
            raw = _call_groq(prompt, system)
            logger.info(f"[LLM] Groq Llama-3.3-70B responded ({len(raw)} chars)")
            return raw, "groq-llama-3.3-70b"
        except Exception as e:
            errors.append(f"groq-llama-3.3-70b: {e}")
            logger.error("[LLM] All 3 tiers failed.")

        raise RuntimeError("All 3 LLM providers failed.\n" + "\n".join(errors))

    @classmethod
    def generate_dual_output(cls, user_prompt: str) -> Tuple[DualOutputPayload, str]:
        """
        Generates a DualOutputPayload (python_code + parameters) from a natural language prompt.
        Returns (DualOutputPayload, model_name_used).
        """
        raw, model_used = cls._call_with_fallback(user_prompt)
        payload = _parse_response(raw)
        logger.info(
            f"[LLM] Generated '{payload.part_name}' | "
            f"{len(payload.parameters)} params | model={model_used}"
        )
        return payload, model_used

    @classmethod
    def correct_code(
        cls,
        user_prompt: str,
        failed_code: str,
        error_traceback: str
    ) -> Tuple[DualOutputPayload, str]:
        """
        Sends the broken script + traceback back to LLM for automated self-correction.
        Truncates traceback from the END (most informative part) to avoid token bloat.
        Returns (corrected_DualOutputPayload, model_name_used).
        """
        # Take the LAST 1500 chars — exception message is always at the end of a traceback
        truncated_traceback = error_traceback[-1500:] if len(error_traceback) > 1500 else error_traceback

        correction_prompt = CORRECTION_PROMPT_TEMPLATE.format(
            user_prompt=user_prompt,
            failed_code=failed_code,
            error_traceback=truncated_traceback
        )
        logger.info("[LLM] Sending self-correction prompt...")
        raw, model_used = cls._call_with_fallback(correction_prompt)
        payload = _parse_response(raw)
        logger.info(f"[LLM] Correction successful | model={model_used}")
        return payload, model_used

    # Expose parser for tests
    @staticmethod
    def _parse_response(raw_json: str) -> DualOutputPayload:
        return _parse_response(raw_json)
