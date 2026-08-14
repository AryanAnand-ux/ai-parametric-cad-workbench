/**
 * App.jsx — AI-Driven Parametric CAD Workbench App Shell
 * Features:
 *   - Natural language prompt submission to /api/generate
 *   - Sub-200ms debounced parametric recomputation via /api/recompute
 *   - React Three Fiber 3D WebGL preview (STL)
 *   - STEP & STL download buttons
 *   - Model info, metrics, and error state handling
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import Viewer3D from './components/Viewer3D';
import ParameterSlider from './components/ParameterSlider';
import { generatePart, recomputePart, healthCheck } from './api';

// Build a full URL for file downloads (works via Vite proxy in dev)
const fileUrl = (path) => path ? `${import.meta.env.VITE_API_URL || ''}${path}` : null;

const PRESET_PROMPTS = [
  "A mounting bracket with four corner M5 holes",
  "A hollow cylinder with 20mm radius and 3mm wall thickness",
  "A rectangular box 60mm x 40mm x 25mm with chamfered top edges",
  "An L-bracket with two perpendicular 60mm arms",
  "A flanged bushing with 10mm inner bore and 20mm outer flange"
];

export default function App() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [recomputing, setRecomputing] = useState(false);
  const [error, setError] = useState(null);

  // Response state from /api/generate
  const [scriptId, setScriptId] = useState(null);
  const [partName, setPartName] = useState(null);
  const [description, setDescription] = useState(null);
  const [pythonCode, setPythonCode] = useState(null);
  const [parameters, setParameters] = useState([]);
  const [paramValues, setParamValues] = useState({});
  const [meshUrl, setMeshUrl] = useState(null);
  const [stepUrl, setStepUrl] = useState(null);
  const [meshInfo, setMeshInfo] = useState(null);
  const [recompTime, setRecompTime] = useState(null);
  const [modelUsed, setModelUsed] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking');

  // Debounce timer for slider recomputation
  const debounceTimerRef = useRef(null);

  // Health check on mount + debounce timer cleanup on unmount
  useEffect(() => {
    healthCheck()
      .then((data) => setBackendStatus(data.status === 'online' ? 'online' : 'offline'))
      .catch(() => setBackendStatus('offline'));

    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    };
  }, []);

  // Submit prompt -> /api/generate
  const handleGenerate = async (overridePrompt) => {
    const activePrompt = overridePrompt || prompt;
    if (!activePrompt.trim() || loading) return;

    setLoading(true);
    setError(null);

    try {
      const res = await generatePart(activePrompt);
      setScriptId(res.script_id);
      setPartName(res.part_name);
      setDescription(res.description);
      setPythonCode(res.python_code);
      setParameters(res.parameters || []);
      setMeshUrl(res.mesh_url);
      setStepUrl(res.step_url);
      setMeshInfo(res.mesh_info || {});
      setRecompTime(res.recomputation_time_ms);
      setModelUsed(res.model_used);

      // Initialize slider values from returned defaults
      const initialValues = {};
      (res.parameters || []).forEach((p) => {
        initialValues[p.name] = p.default;
      });
      setParamValues(initialValues);
    } catch (err) {
      console.error('[Generate error]', err);
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : err.message || 'Generation failed.');
    } finally {
      setLoading(false);
    }
  };

  // Slider change -> fast /api/recompute (<200ms)
  const handleParamChange = useCallback((name, value) => {
    setParamValues((prev) => {
      const nextValues = { ...prev, [name]: value };

      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);

      debounceTimerRef.current = setTimeout(async () => {
        if (!scriptId || !pythonCode) return;
        setRecomputing(true);

        try {
          const res = await recomputePart(scriptId, pythonCode, nextValues);
          setMeshUrl(res.mesh_url);
          setStepUrl(res.step_url);
          setMeshInfo(res.mesh_info || {});
          setRecompTime(res.recomputation_time_ms);
          setError(null);
        } catch (err) {
          console.error('[Recompute error]', err);
          const detail = err.response?.data?.detail;
          const msg = typeof detail === 'string' ? detail : (detail?.error || err.message || 'Recomputation failed.');
          setError(`Recomputation error: ${msg}`);
        } finally {
          setRecomputing(false);
        }
      }, 120); // 120ms debounce for silky smooth updates

      return nextValues;
    });
  }, [scriptId, pythonCode]);

  return (
    <div className="app-shell">
      {/* ── HEADER ──────────────────────────────────────────────── */}
      <header className="header">
        <div className="header-logo">
          <div className="header-logo-icon">⚙️</div>
          <span>AI CAD Workbench</span>
          <span className="header-badge">WEEK 5 — BUILD123D + RAG</span>
        </div>

        <div className="header-actions">
          <span style={{ fontSize: '11px', color: backendStatus === 'online' ? 'var(--success)' : 'var(--error)' }}>
            ● Backend {backendStatus}
          </span>
        </div>
      </header>

      {/* ── SIDEBAR ─────────────────────────────────────────────── */}
      <aside className="sidebar">
        {/* Prompt Input Section */}
        <div className="sidebar-section">
          <div className="sidebar-label">Natural Language Prompt</div>
          <div className="prompt-area">
            <textarea
              id="prompt-input"
              className="prompt-textarea"
              placeholder="e.g. A mounting bracket with four M5 corner holes..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                  e.preventDefault();
                  if (!loading && prompt.trim()) handleGenerate();
                }
              }}
            />

            <button
              id="btn-generate"
              className="generate-btn"
              onClick={() => handleGenerate()}
              disabled={loading || !prompt.trim()}
            >
              {loading ? (
                <>
                  <div className="spinner" />
                  <span>RAG + Generating CAD...</span>
                </>
              ) : (
                <>
                  <span>✨ Generate 3D Part</span>
                </>
              )}
            </button>
          </div>

          {/* Quick preset chips */}
          <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <span className="sidebar-label" style={{ marginBottom: 0 }}>Try an example</span>
            {PRESET_PROMPTS.slice(0, 3).map((p, idx) => (
              <button
                key={idx}
                style={{
                  textAlign: 'left',
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-secondary)',
                  padding: '6px 10px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '11px',
                  cursor: 'pointer'
                }}
                onClick={() => {
                  setPrompt(p);
                  handleGenerate(p);
                }}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Parameters Sliders Section */}
        <div className="params-scroll">
          <div className="sidebar-label">
            Parametric Controls {recomputing && <span style={{ color: 'var(--accent)', marginLeft: '6px' }}>(updating...)</span>}
          </div>

          {parameters.length === 0 ? (
            <div className="no-params-msg">
              Generate a part to unlock real-time parametric sliders.
            </div>
          ) : (
            parameters.map((p) => (
              <ParameterSlider
                key={p.name}
                param={p}
                value={paramValues[p.name] ?? p.default}
                onChange={handleParamChange}
              />
            ))
          )}
        </div>

        {/* Model Metrics Footer */}
        {scriptId && (
          <div className="model-info">
            <div className="info-row">
              <span className="info-key">Script ID</span>
              <span className="info-val">{scriptId}</span>
            </div>
            <div className="info-row">
              <span className="info-key">AI Model</span>
              <span className="info-val accent">{modelUsed || 'build123d RAG'}</span>
            </div>
            <div className="info-row">
              <span className="info-key">Recompute Time</span>
              <span className="info-val success">{recompTime} ms</span>
            </div>
          </div>
        )}
      </aside>

      {/* ── VIEWER AREA ────────────────────────────────────────── */}
      <main className="viewer-area">
        {/* Floating Part Name Badge */}
        {partName && (
          <div className="part-name-badge">
            {partName}
            {description && <span className="part-desc">{description}</span>}
          </div>
        )}

        {/* Download Buttons */}
        {meshUrl && (
          <div className="viewer-toolbar">
            <a
              id="btn-download-stl"
              href={fileUrl(meshUrl)}
              download={`${partName || 'part'}.stl`}
              className="toolbar-btn"
            >
              📥 Download STL
            </a>
            {stepUrl && (
              <a
                id="btn-download-step"
                href={fileUrl(stepUrl)}
                download={`${partName || 'part'}.step`}
                className="toolbar-btn"
              >
                📐 Download STEP
              </a>
            )}
          </div>
        )}

        {/* 3D WebGL Canvas */}
        <Viewer3D meshUrl={meshUrl} loading={loading} />

        {/* Empty State Overlay */}
        {!meshUrl && !loading && (
          <div className="viewer-empty">
            <div className="viewer-empty-icon">🧊</div>
            <div className="viewer-empty-title">Interactive 3D Workbench</div>
            <div className="viewer-empty-sub">
              Enter a prompt on the left or select a preset example to generate a parametric 3D CAD model.
            </div>
          </div>
        )}

        {/* Loading Overlay */}
        {loading && (
          <div className="loading-overlay">
            <div className="spinner" style={{ width: '32px', height: '32px', borderWidth: '3px' }} />
            <div className="loading-title">Retrieving RAG Examples & Building Geometry...</div>
            <div className="loading-dots">
              <div className="loading-dot" />
              <div className="loading-dot" />
              <div className="loading-dot" />
            </div>
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <div className="error-banner">
            ⚠️ {error}
          </div>
        )}

        {/* Mesh Metrics Floating Bar */}
        {meshInfo && meshInfo.dimensions_mm && (
          <div className="mesh-stats">
            <div className="mesh-stat">
              <span className="mesh-stat-val">{meshInfo.dimensions_mm.x} × {meshInfo.dimensions_mm.y} × {meshInfo.dimensions_mm.z}</span>
              <span className="mesh-stat-key">Bounding (mm)</span>
            </div>
            {meshInfo.volume_mm3 && (
              <div className="mesh-stat">
                <span className="mesh-stat-val">{(meshInfo.volume_mm3 / 1000).toFixed(1)} cm³</span>
                <span className="mesh-stat-key">Volume</span>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
