"""
LLM Service — 3-Tier Dual-Model Strategy with RAG Context Injection
====================================================================
Tier 1 (Primary)   : Gemini 2.0 Flash  (google-genai, native JSON mode, free tier)
Tier 2 (Secondary) : Gemini 2.5 Flash  (google-genai, separate quota pool)
Tier 3 (Fallback)  : Groq Llama-3.3-70B (10x faster inference, always-on free tier)

Flow:
  1. Retrieve top-3 similar build123d CAD examples from ChromaDB via RAG.
  2. Dynamically construct system prompt with few-shot example block.
  3. Try Gemini 2.0 Flash first.
  4. Fallback to Gemini 2.5 Flash if quota/rate limited.
  5. Fallback to Groq Llama-3.3-70B if both Gemini fail.
  6. Self-correction loop (up to 3 retries) on execution error.
"""

import os
import json
import logging
from typing import Tuple, Optional

from pydantic import ValidationError

from config import GEMINI_API_KEY, GROQ_API_KEY
from schemas import DualOutputPayload
from services.prompts import BUILD123D_SYSTEM_PROMPT, CORRECTION_PROMPT_TEMPLATE, MODIFY_PROMPT_TEMPLATE
from services.rag_service import RAGService

logger = logging.getLogger("cad_workbench.llm_service")


# ---------------------------------------------------------------------------
# Response Parser (shared by all model tiers)
# ---------------------------------------------------------------------------

import re
import ast

# ---------------------------------------------------------------------------
# Robust Response Parser (Handles escaped/unescaped quotes and control chars)
# ---------------------------------------------------------------------------

def _robust_parse_json(text: str) -> dict:
    """Attempts standard json.loads, then non-strict, then regex field recovery with AST verification."""
    # 1. Standard strict parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2. Non-strict parse (allows unescaped control chars / newlines)
    try:
        return json.loads(text, strict=False)
    except Exception:
        pass

    # 3. Regex extraction fallback for large Python scripts in JSON
    extracted = {}

    # Extract part_name
    m_name = re.search(r'"part_name"\s*:\s*"([^"]+)"', text)
    if m_name:
        extracted["part_name"] = m_name.group(1).strip()
    else:
        extracted["part_name"] = "Parametric Part"

    # Extract description
    m_desc = re.search(r'"description"\s*:\s*"([^"]+)"', text)
    if m_desc:
        extracted["description"] = m_desc.group(1).strip()
    else:
        extracted["description"] = "Parametric 3D CAD model"

    # Extract parameters array using bracket-depth counting
    m_params_start = re.search(r'"parameters"\s*:\s*\[', text)
    if m_params_start:
        start_bracket = m_params_start.end() - 1
        depth = 0
        end_bracket = -1
        in_str = False
        escape = False
        for i in range(start_bracket, len(text)):
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
                if ch == '[':
                    depth += 1
                elif ch == ']':
                    depth -= 1
                    if depth == 0:
                        end_bracket = i + 1
                        break
        if end_bracket != -1:
            try:
                raw_params = text[start_bracket:end_bracket]
                extracted["parameters"] = json.loads(raw_params, strict=False)
            except Exception:
                extracted["parameters"] = []
    else:
        extracted["parameters"] = []

    # Extract python_code string (handles raw multiline python code and escaped quotes)
    code_str = None
    patterns = [
        # Pattern 1: Lookahead for next known JSON field or closing brace
        r'"python_code"\s*:\s*"(.*?)(?="\s*,\s*"(?:parameters|part_name|description)|"\s*\}|",\s*[\r\n])',
        # Pattern 2: Standard JSON string with escaped quotes
        r'"python_code"\s*:\s*"((?:[^"\\]|\\.)*)"',
        # Pattern 3: Greedy match up to end of input
        r'"python_code"\s*:\s*"(.*)'
    ]
    for pat in patterns:
        m_code = re.search(pat, text, re.DOTALL)
        if m_code:
            candidate = m_code.group(1).rstrip('",}')
            candidate = candidate.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
            try:
                ast.parse(candidate)
                code_str = candidate
                break
            except SyntaxError:
                continue

    if code_str:
        extracted["python_code"] = code_str

    # If parameters array failed to parse but python_code has PARAMS, auto-recover parameters
    if (not extracted.get("parameters")) and "python_code" in extracted:
        m_dict = re.search(r"PARAMS\s*=\s*(\{.*?\n\})", extracted["python_code"], re.DOTALL)
        if m_dict:
            try:
                # Safe evaluation of basic literals
                import ast as py_ast
                dict_node = py_ast.literal_eval(m_dict.group(1))
                if isinstance(dict_node, dict):
                    recovered = []
                    for k, v in dict_node.items():
                        if isinstance(v, (int, float)):
                            val = float(v)
                            recovered.append({
                                "name": k,
                                "label": k.replace("_", " ").title(),
                                "type": "number",
                                "default": val,
                                "min": round(val * 0.2, 2) if val > 0 else 0.0,
                                "max": round(val * 3.0, 2) if val > 0 else 100.0,
                                "step": 1.0 if val >= 10 else 0.1
                            })
                    if recovered:
                        extracted["parameters"] = recovered
            except Exception:
                pass

    if "python_code" in extracted and len(extracted["python_code"]) > 20:
        return extracted

    raise ValueError(f"Could not parse valid JSON or recover valid Python AST from LLM response:\n{text[:400]}")


def _parse_response(raw_text: str) -> DualOutputPayload:
    """
    Parses raw LLM text into a validated DualOutputPayload.
    Handles markdown fences and formatting variations gracefully.
    """
    text = raw_text.strip()

    # Strip markdown fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()

    data = _robust_parse_json(text)

    try:
        return DualOutputPayload(**data)
    except (ValidationError, TypeError) as e:
        raise ValueError(f"Response failed schema validation: {e}")


# ---------------------------------------------------------------------------
# Gemini Client (Tier 1: gemini-2.5-flash, Tier 2: gemini-3.7-flash, Tier 3: gemini-flash-latest)
# ---------------------------------------------------------------------------

def _call_gemini(prompt: str, system: str, model: str = "gemini-2.5-flash") -> str:
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
# Groq Client (Tier 4 Fallback: llama-3.3-70b-versatile)
# ---------------------------------------------------------------------------

def _call_groq(prompt: str, system: str) -> str:
    """
    Calls Groq Llama-3.3-70B as a high-speed tertiary fallback.
    Uses JSON mode enforcement via response_format.
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
        max_tokens=8192,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Main LLM Service Class
# ---------------------------------------------------------------------------

class LLMService:
    """
    4-Tier LLM orchestrator with build123d context and RAG dynamic few-shot injection.
    """

    MAX_RETRIES = 3

    @classmethod
    def _construct_system_prompt(cls, user_prompt: str) -> str:
        """
        Retrieves top-3 RAG examples for user_prompt and injects into BUILD123D_SYSTEM_PROMPT.
        """
        try:
            rag_examples = RAGService.retrieve(user_prompt, k=3)
            examples_block = RAGService.format_for_prompt(rag_examples)
        except Exception as e:
            logger.warning(f"[RAG] Failed to retrieve RAG examples: {e}")
            examples_block = ""

        return BUILD123D_SYSTEM_PROMPT.replace("{rag_examples_block}", examples_block)

    @classmethod
    def _call_with_fallback(cls, prompt: str, system: str) -> Tuple[DualOutputPayload, str]:
        """
        4-tier fallback chain with inline schema parsing and validation.
        Returns (DualOutputPayload, model_name_used).
        """
        errors = []

        # --- Tier 1: Gemini 2.5 Flash ---
        try:
            logger.info("[LLM] Calling Gemini 2.5 Flash (Tier 1)...")
            raw = _call_gemini(prompt, system, model="gemini-2.5-flash")
            logger.info(f"[LLM] Gemini 2.5 Flash responded ({len(raw)} chars)")
            payload = _parse_response(raw)
            return payload, "gemini-2.5-flash"
        except Exception as e:
            errors.append(f"gemini-2.5-flash: {e}")
            logger.warning(f"[LLM] Tier 1 failed or invalid JSON: {e}")

        # --- Tier 2: Gemini 3.7 Flash ---
        try:
            logger.info("[LLM] Calling Gemini 3.7 Flash (Tier 2)...")
            raw = _call_gemini(prompt, system, model="gemini-3.7-flash")
            logger.info(f"[LLM] Gemini 3.7 Flash responded ({len(raw)} chars)")
            payload = _parse_response(raw)
            return payload, "gemini-3.7-flash"
        except Exception as e:
            errors.append(f"gemini-3.7-flash: {e}")
            logger.warning(f"[LLM] Tier 2 failed or invalid JSON: {e}")

        # --- Tier 3: Gemini Flash Latest ---
        try:
            logger.info("[LLM] Calling Gemini Flash Latest (Tier 3)...")
            raw = _call_gemini(prompt, system, model="gemini-flash-latest")
            logger.info(f"[LLM] Gemini Flash Latest responded ({len(raw)} chars)")
            payload = _parse_response(raw)
            return payload, "gemini-flash-latest"
        except Exception as e:
            errors.append(f"gemini-flash-latest: {e}")
            logger.warning(f"[LLM] Tier 3 failed or invalid JSON: {e}")

        # --- Tier 4: Groq Llama-3.3-70B ---
        try:
            logger.info("[LLM] Calling Groq Llama-3.3-70B (Tier 4)...")
            raw = _call_groq(prompt, system)
            logger.info(f"[LLM] Groq Llama-3.3-70B responded ({len(raw)} chars)")
            payload = _parse_response(raw)
            return payload, "groq-llama-3.3-70b"
        except Exception as e:
            errors.append(f"groq-llama-3.3-70b: {e}")
            logger.error("[LLM] All 4 tiers failed.")

        raise RuntimeError("All LLM providers failed.\n" + "\n".join(errors))

    @classmethod
    def generate_dual_output(cls, user_prompt: str) -> Tuple[DualOutputPayload, str]:
        """
        Generates a DualOutputPayload (python_code + parameters) for build123d.
        Uses RAG to dynamically retrieve few-shot examples for the system prompt.
        Returns (DualOutputPayload, model_name_used).
        """
        system = cls._construct_system_prompt(user_prompt)
        
        # If user mentions incompatible legacy frameworks (FreeCAD, OpenSCAD, etc.),
        # guide the LLM to emit build123d on the very first pass without failing the AST sandbox.
        effective_prompt = user_prompt
        if re.search(r"\b(freecad|openscad|cadquery|solidworks|catia)\b", user_prompt, re.IGNORECASE):
            effective_prompt = (
                f"{user_prompt}\n\n"
                f"[SYSTEM DIRECTIVE: The user mentions another CAD tool above, but our execution environment is exclusively "
                f"`build123d` (OpenCASCADE). You MUST output 100% valid `build123d` Python code following the 15 rules. "
                f"DO NOT import FreeCAD, Part, or cadquery.]"
            )

        payload, model_used = cls._call_with_fallback(effective_prompt, system=system)
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
        Sends broken build123d script + traceback back to LLM for self-correction.
        """
        truncated_traceback = error_traceback[-1500:] if len(error_traceback) > 1500 else error_traceback

        correction_prompt = CORRECTION_PROMPT_TEMPLATE.format(
            user_prompt=user_prompt,
            failed_code=failed_code,
            error_traceback=truncated_traceback
        )
        system = cls._construct_system_prompt(user_prompt)
        logger.info("[LLM] Sending build123d self-correction prompt...")
        payload, model_used = cls._call_with_fallback(correction_prompt, system=system)
        logger.info(f"[LLM] Correction successful | model={model_used}")
        return payload, model_used

    @classmethod
    def modify_code(
        cls,
        python_code: str,
        modification_prompt: str,
        part_name: str,
        existing_parameters: list,
    ) -> Tuple[DualOutputPayload, str]:
        """
        Modifies an existing build123d script based on a user's natural language change request.
        Preserves PARAMS block structure and variable names where possible.
        Returns (DualOutputPayload, model_name_used).
        """
        import json as _json

        existing_params_json = _json.dumps(
            [p.model_dump() if hasattr(p, 'model_dump') else p for p in existing_parameters],
            indent=2
        )

        modify_prompt = MODIFY_PROMPT_TEMPLATE.format(
            part_name=part_name,
            modification_prompt=modification_prompt,
            python_code=python_code,
            existing_parameters_json=existing_params_json,
        )

        # Use the existing script's RAG context for system prompt
        system = cls._construct_system_prompt(modification_prompt)
        logger.info(f"[LLM] Sending chat-to-modify prompt: '{modification_prompt[:60]}...'")
        payload, model_used = cls._call_with_fallback(modify_prompt, system=system)
        logger.info(
            f"[LLM] Modified '{payload.part_name}' | "
            f"{len(payload.parameters)} params | model={model_used}"
        )
        return payload, model_used

    @classmethod
    def modify_script(
        cls,
        python_code: str,
        modification_prompt: str,
        part_name: str,
        parameters: list = None,
        existing_parameters: list = None,
    ) -> Tuple[DualOutputPayload, str]:
        """Alias for modify_code supporting both parameter argument names."""
        params = parameters if parameters is not None else (existing_parameters or [])
        return cls.modify_code(
            python_code=python_code,
            modification_prompt=modification_prompt,
            part_name=part_name,
            existing_parameters=params,
        )

    # Expose parser for tests
    @staticmethod
    def _parse_response(raw_json: str) -> DualOutputPayload:
        return _parse_response(raw_json)
