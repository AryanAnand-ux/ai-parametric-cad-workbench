"""
VisionService — Gemini Vision sketch parser for the Sketch-to-CAD pipeline.
=============================================================================
Step 1 of the two-step sketch pipeline:
  1. Parse sketch image via Gemini Vision → extract dimensions, topology, and features
     using strict Geometric Chain-of-Thought (Axis Mapping, Base Profile Type,
     Curve Rule, and Feature Elevations).
  2. Return a ParsedSketch with a rich `derived_prompt` that feeds directly
     into the existing LLMService.generate_dual_output() call (Step 2).

Notes:
  - Requires GEMINI_API_KEY; raises RuntimeError if not configured.
  - Image bytes are processed in-memory and never written to disk.
  - Supported MIME types: image/png, image/jpeg, image/webp (Gemini native).
  - Uses Pydantic response_schema with Gemini Structured Outputs to eliminate
    JSON syntax and truncation failures.
"""

import json
import logging
import re
from dataclasses import dataclass
from typing import Dict, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("cad_workbench.vision_service")

# ---------------------------------------------------------------------------
# Pydantic Structured Output Schema for Gemini Vision
# ---------------------------------------------------------------------------

class SketchVisionAnalysis(BaseModel):
    """Structured Geometric Chain-of-Thought output from Gemini Vision."""

    visual_interpretation: str = Field(
        ...,
        description="Concise summary of the mechanical part, its primary function, and main geometry (under 120 chars).",
    )
    axis_mapping: str = Field(
        ...,
        description="Explicit mapping of physical dimensions to 3D axes: X (Width/Length), Y (Depth/Extrusion), Z (Height).",
    )
    base_profile_strategy: str = Field(
        ...,
        description="Whether the primary shape is best formed by 3D primitives (Box, Cylinder) or an extruded 2D sketched profile.",
    )
    curve_strategy: str = Field(
        ...,
        description=(
            "Handling of arches, U-shapes, sweeps, or rounded transitions "
            "(e.g. 2D profile with Line and RadiusArc/ThreePointArc, NOT Box-minus-Box boolean subtraction)."
        ),
    )
    feature_elevations: str = Field(
        ...,
        description="Explicit attachment Z-heights of all secondary features (flanges, bosses, brackets, holes) relative to Z=0.",
    )
    structural_specification: str = Field(
        ...,
        description="Step-by-step structural blueprint of primary body, feature attachments, cuts, chamfers, and through-holes.",
    )
    identified_parameters: Dict[str, float] = Field(
        ...,
        description="Key numeric dimensions in mm or degrees as a snake_case dictionary.",
    )
    derived_prompt: str = Field(
        ...,
        description=(
            "Comprehensive, self-contained engineering prompt for build123d CAD generation "
            "incorporating all axes, dimensions, curve rules, and feature elevations."
        ),
    )


# ---------------------------------------------------------------------------
# Expert system prompt sent to Gemini Vision
# ---------------------------------------------------------------------------

_VISION_SYSTEM_PROMPT = """
Role: You are an expert Computer-Aided Design (CAD) visual parser and build123d geometric reasoning engine.
Goal: Analyze a mechanical sketch or 2D engineering drawing (isometric, orthographic, annotated dimensions, or hand-drawn blueprints) and produce a precise, parameter-driven structural specification for build123d solid modeling.

Analyze the image strictly following this Geometric Chain-of-Thought:

1. Axis Mapping:
   - Explicitly define what physical dimension maps to X (Width/Length), Y (Depth/Extrusion direction), and Z (Height).

2. Base Profile Type:
   - Determine if the main body is best built from basic 3D primitives (Box, Cylinder) OR a 2D sketched profile extruded along an axis.

3. Curve Rule (CRITICAL):
   - If you see an arch, U-shape, curved bracket, or swept curve: DO NOT use Boolean subtraction (e.g. Box minus Box).
   - You MUST identify the need for a 2D sketch profile using closed wires with `Line()` and `RadiusArc()` or `ThreePointArc()`, or curved path sweeps.

4. Feature Elevations (Z-Axis):
   - Explicitly identify the attachment height of all secondary features (flanges, bosses, brackets, holes).
   - State whether they attach at the bottom (Z=0), middle, or top (Z=height) of the main body.

5. Structural Specification:
   - Produce a logical breakdown of the 3D topology: primary shape generation plan, exact attachment locations, cuts, slots, through-holes.

6. Identified Parameters:
   - Extract all discovered dimensions into a snake_case dictionary with values in millimetres (mm) or degrees.
   - Convert inches if needed (1 inch = 25.4 mm). Limit to the 12 most critical dimensions.

7. Derived Prompt:
   - Synthesize a comprehensive, self-contained engineering prompt for build123d CAD generation.
   - Combine all dimensions, coordinate mappings, curve modeling rules, and feature elevations so the downstream CAD generator produces an exact solid without guessing.
""".strip()

_VISION_DEFAULT_USER_TEXT = "Analyze this mechanical sketch and extract the complete CAD structural specification."


# ---------------------------------------------------------------------------
# ParsedSketch result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ParsedSketch:
    """Result of VisionService.parse_sketch()."""
    visual_interpretation: str
    identified_parameters: Dict[str, float]
    derived_prompt: str
    axis_mapping: str = ""
    base_profile_strategy: str = ""
    curve_strategy: str = ""
    feature_elevations: str = ""
    structural_specification: str = ""


# ---------------------------------------------------------------------------
# Robust JSON parsing utilities (used as fallback if response_schema is unavailable)
# ---------------------------------------------------------------------------

def _extract_string_field(text: str, field_name: str) -> Optional[str]:
    """
    Extract a JSON string field using regex.
    Handles escaped quotes and gracefully handles truncated strings.
    """
    pattern = rf'"{re.escape(field_name)}"\s*:\s*"((?:[^"\\]|\\.)*?)"'
    m = re.search(pattern, text, re.DOTALL)
    if m:
        val = m.group(1)
        val = (val.replace('\\"', '"')
                  .replace('\\n', ' ')
                  .replace('\\t', ' ')
                  .replace('\\r', ' ')
                  .replace('\\\\', '\\'))
        return val.strip() or None

    m2 = re.search(rf'"{re.escape(field_name)}"\s*:\s*"(.*)', text, re.DOTALL)
    if m2:
        val = m2.group(1)
        val = re.sub(r'[",\s}\]]+$', '', val).strip()
        val = (val.replace('\\"', '"')
                  .replace('\\n', ' ')
                  .replace('\\t', ' ')
                  .replace('\\r', ' ')
                  .replace('\\\\', '\\'))
        return val.strip() if len(val) > 15 else None

    return None


def _extract_params_dict(text: str) -> Dict[str, float]:
    """Extract identified_parameters dict using brace-depth counting or key:value regex."""
    m = re.search(r'"identified_parameters"\s*:\s*\{', text)
    if m:
        start = m.end() - 1
        depth = 0
        end = -1
        in_str = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if escape:
                escape = False
                continue
            if ch == '\\':
                escape = True
                continue
            if ch == '"':
                in_str = not in_str
                continue
            if not in_str:
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break

        if end != -1:
            try:
                raw_dict = text[start:end]
                return {
                    k: float(v)
                    for k, v in json.loads(raw_dict).items()
                    if isinstance(v, (int, float))
                }
            except Exception:
                pass

        snippet = text[start:]
        result = {}
        for km in re.finditer(r'"([a-z][a-z0-9_]*)"\s*:\s*([0-9]+(?:\.[0-9]+)?)', snippet):
            try:
                result[km.group(1)] = float(km.group(2))
            except ValueError:
                pass
        return result

    result = {}
    skip = {
        "visual_interpretation", "derived_prompt", "identified_parameters",
        "axis_mapping", "base_profile_strategy", "curve_strategy",
        "feature_elevations", "structural_specification"
    }
    for km in re.finditer(r'"([a-z][a-z0-9_]{2,})"\s*:\s*([0-9]+(?:\.[0-9]+)?)', text):
        key = km.group(1)
        if key not in skip:
            try:
                result[key] = float(km.group(2))
            except ValueError:
                pass
    return result


def _synthesize_derived_prompt(
    visual_interpretation: str,
    identified_parameters: Dict[str, float],
    axis_mapping: str = "",
    base_profile_strategy: str = "",
    curve_strategy: str = "",
    feature_elevations: str = "",
    structural_specification: str = "",
) -> str:
    """
    Construct a complete derived_prompt combining all geometric analysis fields.
    Guarantees downstream CAD generator has unambiguous instructions.
    """
    parts = []
    base = visual_interpretation.strip() or "Parametric mechanical part"
    parts.append(base)

    if structural_specification and structural_specification.strip():
        parts.append(f"Structure: {structural_specification.strip()}")
    if axis_mapping and axis_mapping.strip():
        parts.append(f"Coordinate axes: {axis_mapping.strip()}")
    if base_profile_strategy and base_profile_strategy.strip():
        parts.append(f"Base profile: {base_profile_strategy.strip()}")
    if curve_strategy and curve_strategy.strip():
        parts.append(f"Curves & Arches: {curve_strategy.strip()}")
    if feature_elevations and feature_elevations.strip():
        parts.append(f"Z-Elevations: {feature_elevations.strip()}")
    if identified_parameters:
        dims = ", ".join(
            f"{k.replace('_', ' ')} {v}mm" for k, v in list(identified_parameters.items())[:12]
        )
        parts.append(f"Dimensions: {dims}.")

    parts.append("Generate a precise parametric build123d solid model.")
    return " ".join(parts)


def _robust_parse_vision(raw: str) -> dict:
    """
    Fallback parser when standard JSON parsing fails.
    Extracts geometric fields, parameters, and synthesizes derived_prompt.
    """
    for strict in (True, False):
        try:
            data = json.loads(raw) if strict else json.loads(raw, strict=False)
            if data.get("derived_prompt"):
                return data
            logger.warning("[VISION] JSON parsed but derived_prompt is empty — synthesizing fallback")
            data["derived_prompt"] = _synthesize_derived_prompt(
                data.get("visual_interpretation", ""),
                {k: float(v) for k, v in (data.get("identified_parameters") or {}).items()
                 if isinstance(v, (int, float))},
                axis_mapping=data.get("axis_mapping", ""),
                base_profile_strategy=data.get("base_profile_strategy", ""),
                curve_strategy=data.get("curve_strategy", ""),
                feature_elevations=data.get("feature_elevations", ""),
                structural_specification=data.get("structural_specification", ""),
            )
            return data
        except Exception:
            pass

    logger.warning("[VISION] JSON parse failed — attempting regex field extraction")
    data: dict = {}

    for field in (
        "derived_prompt", "visual_interpretation", "axis_mapping",
        "base_profile_strategy", "curve_strategy", "feature_elevations",
        "structural_specification"
    ):
        val = _extract_string_field(raw, field)
        if val:
            data[field] = val

    data["identified_parameters"] = _extract_params_dict(raw)

    if data.get("derived_prompt"):
        logger.info(
            f"[VISION] Regex recovery succeeded — derived_prompt length={len(data['derived_prompt'])}"
        )
        return data

    if data.get("visual_interpretation") or data.get("identified_parameters"):
        logger.warning("[VISION] derived_prompt not found — synthesizing from other fields")
        data["derived_prompt"] = _synthesize_derived_prompt(
            data.get("visual_interpretation", ""),
            data.get("identified_parameters", {}),
            axis_mapping=data.get("axis_mapping", ""),
            base_profile_strategy=data.get("base_profile_strategy", ""),
            curve_strategy=data.get("curve_strategy", ""),
            feature_elevations=data.get("feature_elevations", ""),
            structural_specification=data.get("structural_specification", ""),
        )
        return data

    raise ValueError(
        f"Vision response unrecoverable — no usable fields found. "
        f"Raw (first 300 chars): {raw[:300]}"
    )


# ---------------------------------------------------------------------------
# VisionService
# ---------------------------------------------------------------------------

class VisionService:
    """Calls Gemini Vision to parse a sketch image into a structured CAD spec."""

    @staticmethod
    def parse_sketch(
        image_bytes: bytes,
        mime_type: str,
        user_prompt: Optional[str] = None,
    ) -> ParsedSketch:
        """
        Send `image_bytes` to Gemini Vision and return a ParsedSketch.

        Args:
            image_bytes: Raw image bytes (PNG, JPEG, or WEBP).
            mime_type:   MIME type string, e.g. 'image/png'.
            user_prompt: Optional natural-language guidance from the user
                         (e.g. 'Model 2 only' or 'Make base 50mm wider').

        Returns:
            ParsedSketch with visual_interpretation, identified_parameters, derived_prompt,
            and geometric reasoning fields.

        Raises:
            RuntimeError: If GEMINI_API_KEY is not configured.
            ValueError:   If the Vision model returns an unrecoverable response.
        """
        from config import GEMINI_API_KEY
        from google import genai
        from google.genai import types

        if not GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is required for sketch vision parsing. "
                "Set it in backend/.env."
            )

        client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options={"timeout": 90_000},
        )

        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        text_content = _VISION_DEFAULT_USER_TEXT
        if user_prompt and user_prompt.strip():
            text_content += f"\nUser clarification / requirements: {user_prompt.strip()}"
        text_part = types.Part.from_text(text=text_content)

        logger.info(
            f"[VISION] Sending {len(image_bytes):,} byte {mime_type} image to Gemini Vision "
            f"(user_prompt={bool(user_prompt)})..."
        )

        models_to_try = [
            "gemini-3.5-flash-lite",
            "gemini-flash-lite-latest",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.8-flash",
            "gemini-flash-latest",
        ]

        data = None
        last_err = None

        for model_name in models_to_try:
            logger.info(f"[VISION] Attempting model '{model_name}' for sketch parsing...")
            try:
                gen_config = types.GenerateContentConfig(
                    system_instruction=_VISION_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.1,
                )
                if "lite" not in model_name.lower():
                    gen_config.thinking_config = types.ThinkingConfig(thinking_budget=0)

                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[types.Content(role="user", parts=[image_part, text_part])],
                        config=gen_config,
                    )
                except Exception as call_err:
                    # If thinking_config caused an INVALID_ARGUMENT error, retry without it
                    if "INVALID_ARGUMENT" in str(call_err) and gen_config.thinking_config is not None:
                        logger.info(f"[VISION] Retrying '{model_name}' without thinking_config...")
                        gen_config.thinking_config = None
                        response = client.models.generate_content(
                            model=model_name,
                            contents=[types.Content(role="user", parts=[image_part, text_part])],
                            config=gen_config,
                        )
                    else:
                        raise call_err

                raw = (response.text or "").strip()
                if raw.startswith("```"):
                    raw = "\n".join(
                        line for line in raw.splitlines()
                        if not line.strip().startswith("```")
                    ).strip()
                data = _robust_parse_vision(raw)
                logger.info(f"[VISION] Successfully parsed sketch using '{model_name}'")
                break
            except Exception as err:
                logger.warning(
                    f"[VISION] Model '{model_name}' failed ({err}) — attempting next fallback"
                )
                last_err = err

        if data is None:
            raise ValueError(f"All vision models failed. Last error: {last_err}")

        parsed = ParsedSketch(
            visual_interpretation=str(data.get("visual_interpretation", "")).strip(),
            identified_parameters={
                k: float(v)
                for k, v in (data.get("identified_parameters") or {}).items()
                if isinstance(v, (int, float))
            },
            derived_prompt=str(data.get("derived_prompt", "")).strip(),
            axis_mapping=str(data.get("axis_mapping", "")).strip(),
            base_profile_strategy=str(data.get("base_profile_strategy", "")).strip(),
            curve_strategy=str(data.get("curve_strategy", "")).strip(),
            feature_elevations=str(data.get("feature_elevations", "")).strip(),
            structural_specification=str(data.get("structural_specification", "")).strip(),
        )

        if not parsed.derived_prompt:
            parsed.derived_prompt = _synthesize_derived_prompt(
                parsed.visual_interpretation,
                parsed.identified_parameters,
                axis_mapping=parsed.axis_mapping,
                base_profile_strategy=parsed.base_profile_strategy,
                curve_strategy=parsed.curve_strategy,
                feature_elevations=parsed.feature_elevations,
                structural_specification=parsed.structural_specification,
            )

        if not parsed.derived_prompt:
            raise ValueError(
                "Vision model did not return a usable `derived_prompt`. "
                "The image may be unreadable or not a mechanical drawing."
            )

        logger.info(
            f"[VISION] Parsed OK: {len(parsed.identified_parameters)} parameters | "
            f"prompt='{parsed.derived_prompt[:80]}...'"
        )
        return parsed
