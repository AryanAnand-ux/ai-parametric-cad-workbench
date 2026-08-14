/**
 * api.js — API client for the CAD Workbench backend
 *
 * In development: Vite proxies /api/* and /static/* to http://localhost:8000
 * In production:  Set VITE_API_URL env var (e.g. https://your-backend.com)
 */

import axios from 'axios';

// Use empty string in dev (Vite proxy handles it).
// In production, set VITE_API_URL in frontend/.env
const BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000,   // 120s — LLM + build123d can be slow on cold start
});

/**
 * Generate a new parametric CAD part from a natural language prompt.
 * @param {string} prompt
 * @returns {Promise<GenerateResponse>}
 */
export async function generatePart(prompt) {
  const { data } = await api.post('/api/generate', { prompt });
  return data;
}

/**
 * Recompute a part with updated slider values — no LLM call, very fast.
 * @param {string} scriptId
 * @param {string} pythonCode
 * @param {Record<string, number>} updatedParameters
 * @returns {Promise<RecomputeResponse>}
 */
export async function recomputePart(scriptId, pythonCode, updatedParameters) {
  const { data } = await api.post('/api/recompute', {
    script_id: scriptId,
    python_code: pythonCode,
    updated_parameters: updatedParameters,
  });
  return data;
}

/**
 * Health check — verifies backend is online.
 * @returns {Promise<HealthResponse>}
 */
export async function healthCheck() {
  const { data } = await api.get('/api/health');
  return data;
}
