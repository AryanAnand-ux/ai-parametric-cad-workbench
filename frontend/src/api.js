/**
 * api.js — Comprehensive API Client for CAD Workbench
 *
 * Supports:
 * - JWT Auth token injection & refresh
 * - Authentication (Register, Login, Me)
 * - Project & Design Workspace Management
 * - Streaming Generation via SSE (Real-time pipeline phase updates)
 * - Backward-compatible generatePart, recomputePart, modifyPart
 */

import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || '';
const GENERATION_TIMEOUT = Number(import.meta.env.VITE_GENERATION_TIMEOUT_MS || 300_000);

export function resolveAssetUrl(path) {
  if (!path) return null;
  const baseUrl = BASE_URL.replace(/\/+$/, '');
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}${cleanPath}`;
}

// Human-readable message from an API error. FastAPI validation failures
// arrive as a `detail` ARRAY (one entry per field) — without this they
// surface as the useless "Request failed with status code 422".
export function formatApiError(err, fallback = 'Request failed.') {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const msgs = detail.map((d) => {
      if (typeof d === 'string') return d;
      const loc = Array.isArray(d?.loc)
        ? d.loc.filter((x) => x !== 'body').join('.')
        : '';
      const msg = d?.msg || '';
      // Pydantic v2 prefixes messages with "Value error, " — strip it.
      const clean = msg.replace(/^Value error,\s*/i, '');
      return loc ? `${loc}: ${clean}`.trim() : clean;
    }).filter(Boolean);
    if (msgs.length) return msgs.join('; ');
  }
  if (detail?.error) return detail.error;
  return err?.message || fallback;
}

// Token helper
export function getAuthToken() {
  return localStorage.getItem('cad_token');
}

export function getRefreshToken() {
  return localStorage.getItem('cad_refresh_token');
}

export function setAuthToken(token, refreshToken = undefined) {
  if (token) {
    localStorage.setItem('cad_token', token);
  } else {
    localStorage.removeItem('cad_token');
  }
  if (refreshToken !== undefined) {
    if (refreshToken) {
      localStorage.setItem('cad_refresh_token', refreshToken);
    } else {
      localStorage.removeItem('cad_refresh_token');
    }
  }
}

// Token refresh synchronization state
let isRefreshing = false;
let refreshSubscribers = [];

function subscribeTokenRefresh(cb) {
  refreshSubscribers.push(cb);
}

function onRefreshed(newToken) {
  refreshSubscribers.forEach((cb) => cb(newToken));
  refreshSubscribers = [];
}

async function handleTokenRefresh(originalRequest, clientInstance) {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    setAuthToken(null, null);
    return Promise.reject(new Error('No refresh token available.'));
  }

  if (isRefreshing) {
    return new Promise((resolve, reject) => {
      subscribeTokenRefresh((newToken) => {
        if (!newToken) return reject(new Error('Token refresh failed.'));
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        resolve(clientInstance(originalRequest));
      });
    });
  }

  isRefreshing = true;
  try {
    const { data } = await axios.post(`${BASE_URL}/api/auth/refresh`, { refresh_token: refreshToken });
    const newToken = data.access_token;
    const newRefresh = data.refresh_token;
    setAuthToken(newToken, newRefresh);
    onRefreshed(newToken);
    originalRequest.headers.Authorization = `Bearer ${newToken}`;
    return clientInstance(originalRequest);
  } catch (err) {
    setAuthToken(null, null);
    onRefreshed(null);
    return Promise.reject(err);
  } finally {
    isRefreshing = false;
  }
}

const setupResponseInterceptor = (instance) => {
  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;
      if (error.response?.status === 401 && !originalRequest._retry && getRefreshToken()) {
        originalRequest._retry = true;
        try {
          return await handleTokenRefresh(originalRequest, instance);
        } catch (refreshErr) {
          return Promise.reject(refreshErr);
        }
      }
      return Promise.reject(error);
    }
  );
};

// Axios instance with auth interceptor
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
});

api.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
setupResponseInterceptor(api);

const generationApi = axios.create({
  baseURL: BASE_URL,
  timeout: GENERATION_TIMEOUT,
});

generationApi.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
setupResponseInterceptor(generationApi);

const recomputeApi = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000,
});

recomputeApi.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
setupResponseInterceptor(recomputeApi);

// ─── Authentication API ───────────────────────────────────────────────────

export async function registerUser({ email, password, display_name }) {
  const { data } = await api.post('/api/auth/register', {
    email,
    password,
    display_name,
  });
  const token = data.access_token || data.tokens?.access_token;
  const refreshToken = data.refresh_token || data.tokens?.refresh_token;
  if (token) {
    setAuthToken(token, refreshToken);
  }
  return data;
}

export async function loginUser({ email, password }) {
  const { data } = await api.post('/api/auth/login', {
    email,
    password,
  });
  const token = data.access_token || data.tokens?.access_token;
  const refreshToken = data.refresh_token || data.tokens?.refresh_token;
  if (token) {
    setAuthToken(token, refreshToken);
  }
  return data;
}

export async function fetchCurrentUser() {
  const token = getAuthToken();
  if (!token) return null;
  try {
    const { data } = await api.get('/api/auth/me');
    return data.user || data;
  } catch (err) {
    if (err.response?.status === 401) {
      setAuthToken(null, null);
    }
    return null;
  }
}

export function logoutUser() {
  setAuthToken(null, null);
}

// ─── Projects & Workspace API ─────────────────────────────────────────────

export async function listProjects() {
  const { data } = await api.get('/api/projects');
  return data.projects || [];
}

export async function createProject(name, description = '') {
  const { data } = await api.post('/api/projects', { name, description });
  return data.project;
}

export async function getProject(projectId) {
  const { data } = await api.get(`/api/projects/${projectId}`);
  return data;
}

export async function deleteProject(projectId) {
  const { data } = await api.delete(`/api/projects/${projectId}`);
  return data;
}

export async function getGenerationDetail(generationId) {
  const { data } = await api.get(`/api/generations/${generationId}`);
  return data.generation;
}

// ─── CAD Generation API ───────────────────────────────────────────────────

export async function healthCheck() {
  const { data } = await api.get('/api/health');
  return data;
}

export async function generatePart(prompt) {
  const { data } = await generationApi.post('/api/generate', { prompt });
  return data;
}

/**
 * Upload a mechanical sketch image and generate a parametric 3D model from it.
 * Step 1: Gemini Vision parses the sketch → derived_prompt + parameters.
 * Step 2: derived_prompt feeds into the existing CAD generate pipeline.
 *
 * Returns the same GenerateResponse shape as generatePart().
 * @param {File} imageFile - PNG, JPEG, or WEBP sketch file (max 10 MB)
 * @param {string} [prompt] - Optional natural language guidance or dimension adjustments
 * @returns {Promise<GenerateResponse>}
 */
export async function generatePartFromSketch(imageFile, prompt = '') {
  const formData = new FormData();
  formData.append('image', imageFile);
  if (prompt && typeof prompt === 'string' && prompt.trim()) {
    formData.append('prompt', prompt.trim());
  }

  const token = getAuthToken();
  const baseUrl = BASE_URL.replace(/\/+$/, '');

  let response;
  try {
    response = await fetch(`${baseUrl}/api/generate/sketch`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
  } catch (err) {
    throw new Error(`Sketch upload failed: ${err.message}`);
  }

  if (!response.ok) {
    const errJson = await response.json().catch(() => ({ detail: 'Sketch generation failed' }));
    const detail = errJson?.detail;
    const msg =
      typeof detail === 'string'
        ? detail
        : detail?.error || `Server returned ${response.status}`;
    throw new Error(msg);
  }

  return response.json();
}

/**
 * Stream CAD generation with real-time SSE progress events.
 * @param {string} prompt - Part description
 * @param {(event: {phase: string, message: string, progress: number}) => void} onProgress
 * @param {AbortSignal} [signal] - Optional abort signal to cancel the stream
 * @returns {Promise<GenerateResponse>}
 */
export async function generatePartStream(prompt, onProgress, signal) {
  const url = `${BASE_URL.replace(/\/+$/, '')}/api/generate/stream`;
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify({ prompt }),
      signal,
    });
  } catch (err) {
    if (err?.name === 'AbortError') {
      err.aborted = true;
    }
    throw err;
  }

  if (!response.ok) {
    const errJson = await response.json().catch(() => ({ detail: 'Network request failed' }));
    throw new Error(errJson.detail || errJson.error || `Server returned ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let finalResult = null;

  try {
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('data: ')) {
        const jsonStr = trimmed.slice(6);
        try {
          const parsed = JSON.parse(jsonStr);
          if (parsed.phase === 'complete') {
            finalResult = parsed.result;
          } else if (parsed.phase === 'error') {
            throw new Error(parsed.message || parsed.error || 'Generation failed');
          } else if (onProgress) {
            onProgress(parsed);
          }
        } catch (parseErr) {
          if (parseErr.message && !parseErr.message.includes('JSON')) {
            throw parseErr;
          }
        }
      }
    }
  }
  } catch (err) {
    if (err?.name === 'AbortError') {
      err.aborted = true;
    }
    try { reader.cancel(); } catch { /* ignore */ }
    throw err;
  }

  if (!finalResult) {
    if (signal?.aborted) {
      const abortErr = new Error('Generation aborted');
      abortErr.name = 'AbortError';
      abortErr.aborted = true;
      throw abortErr;
    }
    throw new Error('Stream terminated before generation completed');
  }

  return finalResult;
}

export async function recomputePart(
  scriptId,
  pythonCode,
  updatedParameters,
  parameters = [],
  designMode = 'single_solid',
  components = null,
) {
  const { data } = await recomputeApi.post('/api/recompute', {
    script_id: scriptId,
    python_code: pythonCode,
    updated_parameters: updatedParameters,
    parameters,
    design_mode: designMode,
    components,
  });
  return data;
}

export async function modifyPart(
  scriptId,
  pythonCode,
  partName,
  modificationPrompt,
  parameters = [],
  designMode = 'single_solid',
  components = null,
) {
  const { data } = await generationApi.post('/api/modify', {
    script_id: scriptId,
    python_code: pythonCode,
    part_name: partName,
    modification_prompt: modificationPrompt,
    parameters,
    design_mode: designMode,
    components,
  });
  return data;
}

// ---------------------------------------------------------------------------
// Gallery API
// ---------------------------------------------------------------------------

export async function getGallery({ page = 1, perPage = 20, search = '', tag = '', sortBy = 'recent' } = {}) {
  const params = { page, per_page: perPage };
  if (search) params.search = search;
  if (tag) params.tag = tag;
  if (sortBy) params.sort_by = sortBy;
  const { data } = await api.get('/api/gallery', { params });
  return data;
}

export async function publishDesign(generationId, tags = []) {
  const { data } = await api.post(`/api/designs/${generationId}/publish`, tags);
  return data;
}

export async function unpublishDesign(generationId) {
  const { data } = await api.post(`/api/designs/${generationId}/unpublish`);
  return data;
}

export async function likeDesign(generationId) {
  const { data } = await api.post(`/api/designs/${generationId}/like`);
  return data;
}

export async function forkDesign(generationId, projectId = null) {
  const { data } = await api.post(`/api/designs/${generationId}/fork`, null, {
    params: projectId ? { project_id: projectId } : {},
  });
  return data;
}

export async function getMetrics() {
  const { data } = await api.get('/api/metrics');
  return data;
}

// ---------------------------------------------------------------------------
// Download helpers — trigger a browser download via anchor click, mirroring
// the <a href download> export links used throughout the workbench.
// ---------------------------------------------------------------------------

export async function downloadAllFormats(scriptId) {
  const token = getAuthToken();
  try {
    const res = await api.get(`/api/download/${scriptId}/all`, {
      responseType: 'blob',
      params: token ? { token } : {},
    });
    const blob = new Blob([res.data], { type: 'application/zip' });
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = `${scriptId}.zip`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => window.URL.revokeObjectURL(blobUrl), 1000);
  } catch {
    const baseUrl = BASE_URL.replace(/\/+$/, '');
    const url = `${baseUrl}/api/download/${scriptId}/all${token ? `?token=${encodeURIComponent(token)}` : ''}`;
    const link = document.createElement('a');
    link.href = url;
    link.download = `${scriptId}.zip`;
    document.body.appendChild(link);
    link.click();
    link.remove();
  }
}

