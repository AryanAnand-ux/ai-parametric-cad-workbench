/**
 * App.jsx — AI-Driven Parametric CAD Workbench
 *
 * Design System: Technical Neobrutalist Bento (Tilda-inspired)
 *  - Bento Grid layout partitioning Viewport, Sliders, Telemetry HUD, and Chat-to-Modify
 *  - High-contrast 2.5px solid borders with 4px hard drop shadows
 *  - Floating 3D viewport controls: Top / Front / Side / Isometric camera presets
 *  - PBR Material switcher (Machined Aluminum, CAD Blue, Tooling Yellow, Carbon Slate)
 *  - Real-time parametric slider recompute (<200ms) with debounce
 *  - Chat-to-Modify conversational engineering loop
 *  - Telemetry HUD: Watertight Manifold, Solid Body Count, Bounding Envelope, Volume
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import Viewer3D, { MATERIAL_PRESETS } from './components/Viewer3D';
import ParameterSlider from './components/ParameterSlider';
import { generatePart, recomputePart, healthCheck, modifyPart, resolveAssetUrl } from './api';
import { VISUAL_STYLES, VIEWPORT_BACKGROUNDS } from './constants/visualStyles';

// Build a full URL for file downloads / static assets
const fileUrl = (path) => {
  return resolveAssetUrl(path);
};

/** Read the last generated model from localStorage (once at module load). */
function getPersistedModel() {
  try {
    return JSON.parse(localStorage.getItem('cad_last_model') || 'null') || {};
  } catch {
    return {};
  }
}
const _p = getPersistedModel();

// Categorized Preset CAD Prompts
const PRESET_CATEGORIES = [
  {
    category: 'Engineering & Thermal',
    prompts: [
      { label: 'CPU Heatsink', prompt: 'High-performance linear extruded aluminum CPU heatsink with rectangular fin array, thick heat spreader base plate, and 4 corner mounting screw holes' },
      { label: 'Weld Neck Flange', prompt: 'Class 150 weld neck pipe flange with raised face, through bore, tapered welding neck hub, and 8-bolt circle pattern' },
      { label: 'V-Belt Pulley', prompt: 'Single-groove industrial V-belt drive pulley with central hub, shaft bore, keyway slot, web plate, and 38-degree trapezoidal V-groove rim' }
    ]
  },
  {
    category: 'Transmission & Powertrain',
    prompts: [
      { label: 'Spur Gear Blank', prompt: 'Machined industrial spur gear blank with central hub, shaft bore, standard keyway, recessed web, and outer rim with circular lightening holes' },
      { label: 'Stepped Drive Shaft', prompt: 'Three-step mechanical transmission drive shaft with precision bearing journals, central gear seating shoulder, keyway, and retaining circlip groove' },
      { label: 'Spider Coupling', prompt: 'Three-jaw flexible spider shaft coupling hub with central bore, keyway, clamping slit, and interlocking curved drive jaws' }
    ]
  },
  {
    category: 'Aerospace & Robotics',
    prompts: [
      { label: 'Rocket Nozzle', prompt: 'Convergent-divergent supersonic de Laval conical rocket nozzle with combustion chamber injector flange, throat, and conical expansion bell' },
      { label: 'Motor Housing', prompt: 'Brushless electric motor cylindrical stator housing with central bore, front mounting flange with 4-bolt pattern, and longitudinal external cooling ribs' },
      { label: 'Robotic Clevis', prompt: 'Dual-fork 2-axis robotic arm wrist clevis bracket with base actuator mounting plate, twin fork arms, and cross pivot pin bores' },
      { label: 'Quadcopter Frame', prompt: 'A quadcopter drone central chassis plate with 4 diagonal motor arms and M3 motor mounts' }
    ]
  },
  {
    category: 'Enclosures & Fluid',
    prompts: [
      { label: 'Enclosure Box', prompt: 'Rectangular electronics project box bottom enclosure with rounded corners, hollow interior, 4 corner PCB screw standoff bosses, and side cable gland cutout' },
      { label: 'Hydraulic Manifold', prompt: 'High-pressure hydraulic valve subplate manifold block with standard P, T, A, B port counterbores, internal galleries, and mounting holes' },
      { label: 'Mounting Bracket', prompt: 'A mounting bracket with four M5 corner holes, 80x50x5mm with 4mm fillets' }
    ]
  }
];

const QUICK_MODIFICATIONS = [
  'Make walls 2mm thicker',
  'Add 4x M3 corner mounting holes',
  'Add 3mm fillets to all vertical edges',
  'Increase overall length by 20mm'
];

export default function App({ onGoHome }) {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [recomputing, setRecomputing] = useState(false);
  const [error, setError] = useState(null);

  // Response state from /api/generate & /api/modify — restored from localStorage
  const [scriptId, setScriptId] = useState(_p.scriptId ?? null);
  const [partName, setPartName] = useState(_p.partName ?? null);
  const [description, setDescription] = useState(_p.description ?? null);
  const [pythonCode, setPythonCode] = useState(_p.pythonCode ?? null);
  const [parameters, setParameters] = useState(_p.parameters ?? []);
  const [parameterSearch, setParameterSearch] = useState('');
  const [paramValues, setParamValues] = useState(_p.paramValues ?? {});
  const [meshUrl, setMeshUrl] = useState(_p.meshUrl ?? null);
  const [stepUrl, setStepUrl] = useState(_p.stepUrl ?? null);
  const [meshInfo, setMeshInfo] = useState(_p.meshInfo ?? null);
  const [recompTime, setRecompTime] = useState(null);
  const [modelUsed, setModelUsed] = useState(null);
  const [designMode, setDesignMode] = useState(_p.designMode ?? 'single_solid');
  const [components, setComponents] = useState(_p.components ?? null);
  const [backendStatus, setBackendStatus] = useState('checking');

  // Viewport Control States (AutoCAD Engine)
  const [showAxes, setShowAxes] = useState(true);
  const [showGrid, setShowGrid] = useState(true);
  const [materialType, setMaterialType] = useState('cad_gray');
  const [visualStyle, setVisualStyle] = useState('shaded_edges');
  const [backgroundTheme, setBackgroundTheme] = useState('atelier_sand');
  const [cursorCoords, setCursorCoords] = useState({ x: '0.0', y: '0.0', z: '0.0' });
  const [activeCamView, setActiveCamView] = useState('iso');
  const [showCodeModal, setShowCodeModal] = useState(false);
  const viewerRef = useRef(null);

  // Chat-to-Modify state
  const [chatHistory, setChatHistory] = useState([]);
  const [modifyPrompt, setModifyPrompt] = useState('');
  const [modifying, setModifying] = useState(false);
  const chatEndRef = useRef(null);

  // Model undo history — stores last 5 snapshots for undo
  const [modelHistory, setModelHistory] = useState([]);
  const [showDimensions, setShowDimensions] = useState(true);

  // Sidebar collapse
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Viewport dropdown state — which dropdown is open ('style'|'view'|'material'|'export'|null)
  const [openDropdown, setOpenDropdown] = useState(null);
  const dropdownRef = useRef(null);

  // Debounce timer for slider recomputation
  const debounceTimerRef = useRef(null);
  const recomputeSequenceRef = useRef(0);

  // Health check on mount + debounce timer cleanup
  useEffect(() => {
    healthCheck()
      .then((data) => setBackendStatus(data.status === 'online' ? 'online' : 'offline'))
      .catch(() => setBackendStatus('offline'));

    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    };
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    if (!openDropdown) return undefined;
    const handle = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpenDropdown(null);
      }
    };
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, [openDropdown]);

  const toggleDropdown = (key) => setOpenDropdown((prev) => (prev === key ? null : key));

  useEffect(() => {
    if (!showCodeModal) return undefined;
    const handleEscape = (event) => {
      if (event.key === 'Escape') setShowCodeModal(false);
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [showCodeModal]);

  // Sidebar active tab ('sliders' | 'chat' | 'prompt' | 'all')
  const [activeTab, setActiveTab] = useState('all');

  // Apply response from generate or modify + persist to localStorage
  const applyPartResponse = (res) => {
    recomputeSequenceRef.current += 1;
    const initialValues = {};
    (res.parameters || []).forEach((p) => { initialValues[p.name] = p.default; });

    setScriptId(res.script_id);
    setPartName(res.part_name);
    setDescription(res.description);
    setPythonCode(res.python_code);
    setParameters(res.parameters || []);
    setParameterSearch('');
    setMeshUrl(res.mesh_url);
    setStepUrl(res.step_url);
    setMeshInfo(res.mesh_info || {});
    setRecompTime(res.recomputation_time_ms);
    setModelUsed(res.model_used);
    setDesignMode(res.design_mode || 'single_solid');
    setComponents(res.components || null);
    setParamValues(initialValues);

    // Persist model state so page refresh restores the last model
    try {
      localStorage.setItem('cad_last_model', JSON.stringify({
        scriptId: res.script_id,
        partName: res.part_name,
        description: res.description,
        pythonCode: res.python_code,
        parameters: res.parameters || [],
        paramValues: initialValues,
        meshUrl: res.mesh_url,
        stepUrl: res.step_url,
        meshInfo: res.mesh_info || {},
        designMode: res.design_mode || 'single_solid',
        components: res.components || null,
      }));
    } catch (e) {
      console.warn('[Persist] Could not save model to localStorage:', e);
    }

    // Switch to sliders view if parameters are present so they have 100% space
    if (res.parameters && res.parameters.length > 0) {
      setActiveTab('sliders');
    }
  };

  // Submit prompt -> /api/generate
  const handleGenerate = async (overridePrompt) => {
    const activePrompt = overridePrompt || prompt;
    if (!activePrompt.trim() || loading) return;

    setLoading(true);
    setError(null);
    setChatHistory([]);

    try {
      const res = await generatePart(activePrompt);
      applyPartResponse(res);
    } catch (err) {
      console.error('[Generate error]', err);
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : (detail?.error || err.message || 'Generation failed. Check backend log.'));
    } finally {
      setLoading(false);
    }
  };

  // Capture snapshot for undo stack
  const saveSnapshot = () => {
    if (!scriptId || !pythonCode) return;
    setModelHistory((prev) => [
      {
        scriptId,
        partName,
        description,
        pythonCode,
        parameters: [...parameters],
        paramValues: { ...paramValues },
        meshUrl,
        stepUrl,
        meshInfo,
        recompTime,
        modelUsed,
        designMode,
        components,
      },
      ...prev,
    ].slice(0, 5));
  };

  // Undo to previous model state
  const handleUndo = () => {
    if (modelHistory.length === 0) return;
    const [lastState, ...remaining] = modelHistory;
    setModelHistory(remaining);
    setScriptId(lastState.scriptId);
    setPartName(lastState.partName);
    setDescription(lastState.description);
    setPythonCode(lastState.pythonCode);
    setParameters(lastState.parameters || []);
    setParamValues(lastState.paramValues || {});
    setMeshUrl(lastState.meshUrl);
    setStepUrl(lastState.stepUrl);
    setMeshInfo(lastState.meshInfo || {});
    setRecompTime(lastState.recompTime);
    setModelUsed(lastState.modelUsed);
    setDesignMode(lastState.designMode || 'single_solid');
    setComponents(lastState.components || null);
  };

  // Chat-to-Modify -> /api/modify
  const handleModify = async (overrideMsg) => {
    const msg = (overrideMsg || modifyPrompt).trim();
    if (!msg || modifying || !scriptId || !pythonCode) return;
    setModifyPrompt('');
    setModifying(true);
    setError(null);

    setChatHistory((prev) => [...prev, { role: 'user', text: msg }]);

    try {
      saveSnapshot();
      const res = await modifyPart(
        scriptId,
        pythonCode,
        partName || 'Part',
        msg,
        parameters,
        designMode,
        components,
      );
      applyPartResponse(res);
      setChatHistory((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `✅ Applied: "${msg}" — Updated solid model.`,
          model: res.model_used,
        },
      ]);
    } catch (err) {
      console.error('[Modify error]', err);
      const detail = err.response?.data?.detail;
      const msg2 = typeof detail === 'string' ? detail : (detail?.error || err.message || 'Modification failed.');
      setError(`Modify error: ${msg2}`);
      setChatHistory((prev) => [
        ...prev,
        { role: 'assistant', text: `❌ Failed: ${msg2}`, isError: true },
      ]);
    } finally {
      setModifying(false);
      setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    }
  };

  // Slider change -> fast /api/recompute (<200ms)
  const handleParamChange = useCallback((name, value) => {
    const requestSequence = ++recomputeSequenceRef.current;
    setParamValues((prev) => {
      const nextValues = { ...prev, [name]: value };

      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);

      debounceTimerRef.current = setTimeout(async () => {
        if (!scriptId || !pythonCode) return;
        setRecomputing(true);

        try {
          const res = await recomputePart(
            scriptId,
            pythonCode,
            nextValues,
            parameters,
            designMode,
            components,
          );
          if (requestSequence !== recomputeSequenceRef.current) return;
          setMeshUrl(res.mesh_url);
          setStepUrl(res.step_url);
          setMeshInfo(res.mesh_info || {});
          setRecompTime(res.recomputation_time_ms);
          setError(null);
        } catch (err) {
          if (requestSequence !== recomputeSequenceRef.current) return;
          console.error('[Recompute error]', err);
          const detail = err.response?.data?.detail;
          const msg = typeof detail === 'string' ? detail : (detail?.error || err.message || 'Recomputation failed.');
          setError(`Recomputation error: ${msg}`);
        } finally {
          if (requestSequence === recomputeSequenceRef.current) setRecomputing(false);
        }
      }, 120);

      return nextValues;
    });
  }, [parameters, scriptId, pythonCode, designMode, components]);

  // Reset all sliders to defaults AND trigger recompute on canvas
  const handleResetAll = async () => {
    if (!parameters.length || !scriptId || !pythonCode) return;
    const resetVals = {};
    parameters.forEach((p) => { resetVals[p.name] = p.default; });
    const requestSequence = ++recomputeSequenceRef.current;
    setParamValues(resetVals);
    setRecomputing(true);
    try {
      const res = await recomputePart(
        scriptId,
        pythonCode,
        resetVals,
        parameters,
        designMode,
        components,
      );
      if (requestSequence !== recomputeSequenceRef.current) return;
      setMeshUrl(res.mesh_url);
      setStepUrl(res.step_url);
      setMeshInfo(res.mesh_info || {});
      setRecompTime(res.recomputation_time_ms);
      setError(null);
    } catch (err) {
      if (requestSequence !== recomputeSequenceRef.current) return;
      console.error('[Reset error]', err);
      const detail = err.response?.data?.detail;
      const message = typeof detail === 'string' ? detail : (detail?.error || err.message || 'Reset recomputation failed.');
      setError(`Reset error: ${message}`);
    } finally {
      if (requestSequence === recomputeSequenceRef.current) setRecomputing(false);
    }
  };

  const handleCameraPreset = (view) => {
    setActiveCamView(view);
    viewerRef.current?.setCameraView(view);
  };

  return (
    <div className={`app-shell${sidebarOpen ? '' : ' sidebar-collapsed'}`}>
      {/* ── BENTO HEADER ─────────────────────────────────────────── */}
      <header className="header">
        <div className="header-logo">
          <div className="header-logo-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
              <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
              <line x1="12" y1="22.08" x2="12" y2="12"/>
            </svg>
          </div>
          <div>
            <div className="header-title">The CAD Atelier</div>
            <div className="header-subtitle">build123d B-Rep Solid Modeling Kernel</div>
          </div>
          <span className="header-badge">ATELIER SPEC V2.0</span>
        </div>

        {/* ── NAVBAR CAD OPTIONS DROPDOWNS ── */}
        <div className="header-nav-dropdowns" ref={dropdownRef}>
          {/* Visual Style Dropdown */}
          <div className="vt-dropdown">
            <button
              type="button"
              className={`vt-dropdown-trigger ${openDropdown === 'style' ? 'open' : ''}`}
              onClick={() => toggleDropdown('style')}
              title="Change Visual Rendering Style"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 2a10 10 0 0 0 0 20z" fill="currentColor"/>
              </svg>
              <span>{VISUAL_STYLES[visualStyle]?.shortName || 'Style'}</span>
              <span className="chevron">▼</span>
            </button>
            {openDropdown === 'style' && (
              <div className="vt-dropdown-menu">
                <div className="vt-dropdown-label">Visual Style</div>
                {Object.entries(VISUAL_STYLES).map(([key, s]) => (
                  <button
                    key={key}
                    type="button"
                    className={`vt-dropdown-item ${visualStyle === key ? 'active' : ''}`}
                    onClick={() => { setVisualStyle(key); setOpenDropdown(null); }}
                  >
                    <span className="item-dot" />
                    <span>{s.name}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Camera View Dropdown */}
          <div className="vt-dropdown">
            <button
              type="button"
              className={`vt-dropdown-trigger ${openDropdown === 'view' ? 'open' : ''}`}
              onClick={() => toggleDropdown('view')}
              title="Select Camera Orientation"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                <circle cx="12" cy="13" r="4"/>
              </svg>
              <span>{activeCamView === 'iso' ? 'Isometric' : activeCamView.toUpperCase()}</span>
              <span className="chevron">▼</span>
            </button>
            {openDropdown === 'view' && (
              <div className="vt-dropdown-menu">
                <div className="vt-dropdown-label">Camera View</div>
                {[['iso','SE Isometric'],['top','Top View (Z+)'],['front','Front View (Y-)'],['side','Side View (X+)']].map(([v, label]) => (
                  <button
                    key={v}
                    type="button"
                    className={`vt-dropdown-item ${activeCamView === v ? 'active' : ''}`}
                    onClick={() => { handleCameraPreset(v); setOpenDropdown(null); }}
                  >
                    <span className="item-dot" />
                    <span>{label}</span>
                  </button>
                ))}
                <div className="vt-dropdown-sep" />
                <button
                  type="button"
                  className="vt-dropdown-item"
                  onClick={() => { viewerRef.current?.resetView(); setOpenDropdown(null); }}
                >
                  <span className="item-dot" />
                  <span>Fit to View</span>
                </button>
              </div>
            )}
          </div>

          {/* Surface Finish / Material Dropdown */}
          <div className="vt-dropdown">
            <button
              type="button"
              className={`vt-dropdown-trigger ${openDropdown === 'material' ? 'open' : ''}`}
              onClick={() => toggleDropdown('material')}
              title="Change Material Finish & Canvas"
            >
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: MATERIAL_PRESETS[materialType]?.swatch || '#CBD5E1', display: 'inline-block' }} />
              <span>{MATERIAL_PRESETS[materialType]?.name || 'Finish'}</span>
              <span className="chevron">▼</span>
            </button>
            {openDropdown === 'material' && (
              <div className="vt-dropdown-menu">
                <div className="vt-dropdown-label">Surface Material</div>
                {Object.entries(MATERIAL_PRESETS).map(([key, mat]) => (
                  <button
                    key={key}
                    type="button"
                    className={`vt-dropdown-item ${materialType === key ? 'active' : ''}`}
                    onClick={() => { setMaterialType(key); setOpenDropdown(null); }}
                  >
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: mat.swatch, flexShrink: 0, display: 'inline-block' }} />
                    <span>{mat.name}</span>
                  </button>
                ))}
                <div className="vt-dropdown-sep" />
                <div className="vt-dropdown-label">Canvas Environment</div>
                {Object.entries(VIEWPORT_BACKGROUNDS).map(([key, bg]) => (
                  <button
                    key={key}
                    type="button"
                    className={`vt-dropdown-item ${backgroundTheme === key ? 'active' : ''}`}
                    onClick={() => { setBackgroundTheme(key); setOpenDropdown(null); }}
                  >
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: `linear-gradient(135deg,${bg.topColor},${bg.bottomColor})`, flexShrink: 0, display: 'inline-block' }} />
                    <span>{bg.name}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Export Dropdown */}
          <div className="vt-dropdown">
            <button
              type="button"
              className={`vt-dropdown-trigger ${openDropdown === 'export' ? 'open' : ''}`}
              onClick={() => toggleDropdown('export')}
              title={meshUrl || stepUrl ? "Download 3D CAD Files" : "Generate a model first to export"}
              style={{ opacity: (meshUrl || stepUrl || pythonCode) ? 1 : 0.65 }}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              <span>Export</span>
              <span className="chevron">▼</span>
            </button>
            {openDropdown === 'export' && (
              <div className="vt-dropdown-menu">
                <div className="vt-dropdown-label">Download Assets</div>
                {meshUrl ? (
                  <a
                    href={fileUrl(meshUrl)}
                    download={`${partName || 'part'}.stl`}
                    className="vt-dropdown-item"
                    onClick={() => setOpenDropdown(null)}
                  >
                    <span className="item-dot active" />
                    <span>STL Mesh (.stl)</span>
                  </a>
                ) : (
                  <div className="vt-dropdown-item" style={{ opacity: 0.5, cursor: 'not-allowed' }}>
                    <span className="item-dot" />
                    <span>STL Mesh (Generate First)</span>
                  </div>
                )}
                {stepUrl ? (
                  <a
                    href={fileUrl(stepUrl)}
                    download={`${partName || 'part'}.step`}
                    className="vt-dropdown-item"
                    onClick={() => setOpenDropdown(null)}
                  >
                    <span className="item-dot active" />
                    <span>STEP B-Rep (.step)</span>
                  </a>
                ) : (
                  <div className="vt-dropdown-item" style={{ opacity: 0.5, cursor: 'not-allowed' }}>
                    <span className="item-dot" />
                    <span>STEP B-Rep (Generate First)</span>
                  </div>
                )}
                {pythonCode && (
                  <button
                    type="button"
                    className="vt-dropdown-item"
                    onClick={() => { setShowCodeModal(true); setOpenDropdown(null); }}
                  >
                    <span className="item-dot active" />
                    <span>Python CAD Script (.py)</span>
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="header-actions">
          <button
            className="sidebar-toggle-btn"
            onClick={() => setSidebarOpen((v) => !v)}
            title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
            aria-label="Toggle sidebar"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              {sidebarOpen ? <polyline points="15 18 9 12 15 6" /> : <polyline points="9 18 15 12 9 6" />}
            </svg>
          </button>
          {modelHistory.length > 0 && (
            <button
              className="toolbar-btn header-action-btn"
              onClick={handleUndo}
              title={`Undo to previous model state (${modelHistory.length} in stack)`}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 10h10a5 5 0 0 1 5 5v2"/>
                <polyline points="7 6 3 10 7 14"/>
              </svg>
              <span>Undo ({modelHistory.length})</span>
            </button>
          )}
          {pythonCode && (
            <button
              className="toolbar-btn header-action-btn"
              onClick={() => setShowCodeModal(true)}
              title="Inspect Python CAD Script"
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="16 18 22 12 16 6"/>
                <polyline points="8 6 2 12 8 18"/>
              </svg>
              <span>Inspect Code</span>
            </button>
          )}
          <div className="status-pill" style={{ borderColor: backendStatus === 'online' ? '#10B981' : '#EF4444' }}>
            <span
              className="status-dot"
              style={{ background: backendStatus === 'online' ? '#10B981' : '#EF4444' }}
            />
            <span>
              {backendStatus === 'online'
                ? 'CAD Engine Online'
                : backendStatus === 'offline' ? 'CAD Engine Offline' : 'Connecting...'}
            </span>
          </div>
        </div>
      </header>

      {/* ── LEFT BENTO SIDEBAR: CONTROLS & CHAT ──────────────────── */}
      <aside className="sidebar">
        {/* Sidebar Mode Tabs */}
        <div className="sidebar-tabs-nav">
          <button
            type="button"
            className={`sidebar-tab-btn ${activeTab === 'sliders' ? 'active' : ''}`}
            onClick={() => setActiveTab('sliders')}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/>
            </svg>
            <span>Dimensions</span> {parameters.length > 0 && <span className="tab-count-badge">{parameters.length}</span>}
          </button>
          <button
            type="button"
            className={`sidebar-tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
            disabled={!scriptId}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <span>Chat Modify</span> {chatHistory.length > 0 && <span className="tab-count-badge">{chatHistory.length}</span>}
          </button>
          <button
            type="button"
            className={`sidebar-tab-btn ${activeTab === 'prompt' ? 'active' : ''}`}
            onClick={() => setActiveTab('prompt')}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            <span>New Part</span>
          </button>
          <button
            type="button"
            className={`sidebar-tab-btn ${activeTab === 'all' ? 'active' : ''}`}
            onClick={() => setActiveTab('all')}
            title="Show all sections stacked"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
            </svg>
            <span>All</span>
          </button>
        </div>

        {/* Prompt Input Section */}
        {(activeTab === 'all' || activeTab === 'prompt' || !scriptId) && (
          <div className="sidebar-section bento-card">
            <div className="section-header">
              <span className="section-title">Natural Language Prompt</span>
              <span className="section-tag">RAG + LLM</span>
            </div>

            <div className="prompt-area">
              <textarea
                id="prompt-input"
                aria-label="Natural language CAD prompt"
                className="prompt-textarea"
                placeholder="e.g. A mounting plate 100x60x5mm with four M4 corner clearance holes and 5mm edge fillets..."
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
                    <span>RAG Synthesizing Solid...</span>
                  </>
                ) : (
                  <>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                    </svg>
                    <span>Generate Parametric 3D Solid</span>
                  </>
                )}
              </button>
            </div>

            {/* Categorized Quick Presets */}
            <div className="presets-container">
              <div className="preset-tabs-label">Quick Launch Presets:</div>
              <div className="preset-pills-list">
                {PRESET_CATEGORIES.map((cat) =>
                  cat.prompts.map((item, idx) => (
                    <button
                      key={`${cat.category}-${idx}`}
                      className="preset-chip"
                      onClick={() => {
                        setPrompt(item.prompt);
                        handleGenerate(item.prompt);
                      }}
                      title={item.prompt}
                    >
                      <span className="preset-chip-dot" />
                      <span>{item.label}</span>
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Parametric Sliders Section */}
        {(activeTab === 'all' || activeTab === 'sliders') && (
          <div className={`params-scroll bento-card ${activeTab === 'sliders' ? 'bento-card--full' : ''}`}>
            <div className="section-header">
              <div className="section-title">
                Parametric Dimensions
                {parameters.length > 0 && (
                  <span className="section-tag">{parameters.length} Variables</span>
                )}
                {recomputing && <span className="recomputing-tag">Updating...</span>}
              </div>
              {parameters.length > 0 && (
                <button
                  className="preset-chip reset-chip"
                  onClick={handleResetAll}
                  title="Reset all sliders to default dimensions"
                >
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 10h10a5 5 0 0 1 5 5v2"/>
                    <polyline points="7 6 3 10 7 14"/>
                  </svg>
                  <span>Reset</span>
                </button>
              )}
            </div>

            {parameters.length === 0 ? (
              <div className="no-params-msg">
                <div className="empty-sliders-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21.3 15.3l-9.6-9.6a2.4 2.4 0 0 0-3.4 0L2.7 11.3a2.4 2.4 0 0 0 0 3.4l9.6 9.6a2.4 2.4 0 0 0 3.4 0l5.6-5.6a2.4 2.4 0 0 0 0-3.4z"/>
                    <path d="M14.5 9.5l2 2"/>
                    <path d="M11.5 12.5l2 2"/>
                    <path d="M8.5 15.5l2 2"/>
                  </svg>
                </div>
                <div>Generate a solid model to unlock real-time build123d parametric sliders.</div>
                <button
                  className="preset-chip"
                  style={{ marginTop: '8px' }}
                  onClick={() => setActiveTab('prompt')}
                >
                  Choose a Prompt or Preset
                </button>
              </div>
            ) : (
              <>
                {meshInfo && meshInfo.dimensions_mm && (
                  <div className="sidebar-metrics-bar">
                    <span className="sidebar-metric-chip">
                      {meshInfo.dimensions_mm.x} × {meshInfo.dimensions_mm.y} × {meshInfo.dimensions_mm.z} mm
                    </span>
                    {meshInfo.volume_mm3 && (
                      <span className="sidebar-metric-chip">
                        · {(meshInfo.volume_mm3 / 1000).toFixed(1)} cm³
                      </span>
                    )}
                    {meshInfo.is_watertight !== undefined && (
                      <span className="sidebar-metric-chip" style={{ color: meshInfo.is_watertight ? '#10B981' : '#EF4444' }}>
                        · {meshInfo.is_watertight ? 'Watertight' : 'Non-Manifold'}
                      </span>
                    )}
                  </div>
                )}
                <div className="parameter-search-row">
                  <input
                    className="parameter-search-input"
                    type="search"
                    aria-label="Filter parametric dimensions"
                    placeholder="Filter dimensions..."
                    value={parameterSearch}
                    onChange={(event) => setParameterSearch(event.target.value)}
                  />
                  <span className="parameter-match-count">
                    {parameters.filter((p) => `${p.label} ${p.name}`.toLowerCase().includes(parameterSearch.toLowerCase())).length}/{parameters.length}
                  </span>
                </div>
                <div className="sliders-list">
                {parameters.filter((p) => `${p.label} ${p.name}`.toLowerCase().includes(parameterSearch.toLowerCase())).map((p) => (
                  <ParameterSlider
                    key={p.name}
                    param={p}
                    value={paramValues[p.name] ?? p.default}
                    onChange={handleParamChange}
                  />
                ))}
                </div>
              </>
            )}

            {/* Quick Modify Shortcut Bar at bottom of Sliders */}
            {scriptId && (
              <div className="slider-bottom-quick-bar">
                <div className="quick-bar-label">Quick Actions:</div>
                <div className="quick-mods-bar">
                  {QUICK_MODIFICATIONS.slice(0, 3).map((qm, i) => (
                    <button
                      key={i}
                      className="quick-mod-btn"
                      onClick={() => {
                        setActiveTab('chat');
                        handleModify(qm);
                      }}
                      disabled={modifying}
                    >
                      + {qm}
                    </button>
                  ))}
                  <button
                    className="quick-mod-btn quick-mod-btn--chat"
                    onClick={() => setActiveTab('chat')}
                  >
                    Open Chat to Modify →
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Chat-to-Modify Section */}
        {scriptId && (activeTab === 'all' || activeTab === 'chat') && (
          <div className={`chat-panel bento-card ${activeTab === 'chat' ? 'bento-card--full' : ''}`}>
            <div className="section-header">
              <span className="section-title">Chat-to-Modify</span>
              <span className="section-tag">Conversational Delta</span>
            </div>

            {/* Quick Modification Pills */}
            <div className="quick-mods-bar">
              {QUICK_MODIFICATIONS.map((qm, i) => (
                <button
                  key={i}
                  className="quick-mod-btn"
                  onClick={() => handleModify(qm)}
                  disabled={modifying}
                >
                  + {qm}
                </button>
              ))}
            </div>

            {/* Chat Conversation History */}
            {chatHistory.length > 0 && (
              <div className="chat-history">
                {chatHistory.map((msg, i) => (
                  <div
                    key={i}
                    className={`chat-bubble chat-bubble--${msg.role}${msg.isError ? ' chat-bubble--error' : ''}`}
                  >
                    <div className="chat-bubble-header">
                      <span>{msg.role === 'user' ? 'Designer' : 'CAD Kernel'}</span>
                      {msg.model && <span className="chat-bubble-meta">{msg.model}</span>}
                    </div>
                    <div className="chat-bubble-text">{msg.text}</div>
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>
            )}

            {/* Modification Input */}
            <div className="chat-input-row">
              <textarea
                aria-label="CAD modification request"
                className="chat-textarea"
                placeholder='e.g. "Increase flange radius by 5mm" or "Add 2mm chamfer"'
                value={modifyPrompt}
                rows={2}
                onChange={(e) => setModifyPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    handleModify();
                  }
                }}
                disabled={modifying}
              />
              <button
                className="chat-send-btn"
                onClick={() => handleModify()}
                disabled={modifying || !modifyPrompt.trim()}
                title="Apply modification (Ctrl+Enter)"
              >
                {modifying ? (
                  <div className="spinner" style={{ width: '14px', height: '14px' }} />
                ) : (
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="9 18 15 12 9 6"/>
                    </svg>
                    <span>Apply</span>
                  </span>
                )}
              </button>
            </div>
          </div>
        )}
      </aside>

      {/* ── MAIN 3D CAD VIEWPORT & HUD (AutoCAD Engine Mode) ────── */}
      <main
        className="viewer-area"
        style={{
          background: `linear-gradient(180deg, ${VIEWPORT_BACKGROUNDS[backgroundTheme]?.topColor || '#242A35'} 0%, ${VIEWPORT_BACKGROUNDS[backgroundTheme]?.bottomColor || '#12151B'} 100%)`,
        }}
      >
        {/* 3D WebGL Canvas */}
        <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
          <Viewer3D
            ref={viewerRef}
            meshUrl={meshUrl}
            visualStyle={visualStyle}
            backgroundTheme={backgroundTheme}
            materialType={materialType}
            showAxes={showAxes}
            showGrid={showGrid}
            showDimensions={showDimensions}
            onCoordsUpdate={setCursorCoords}
          />
          {/* Recomputing overlay — appears during slow boolean recomputation */}
          {recomputing && (
            <div style={{
              position: 'absolute', inset: 0,
              display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center',
              background: 'rgba(10,12,16,0.65)',
              backdropFilter: 'blur(3px)',
              zIndex: 20,
              gap: '12px',
              pointerEvents: 'none',
            }}>
              <div style={{
                width: 48, height: 48,
                border: '4px solid rgba(255,255,255,0.1)',
                borderTop: '4px solid #60A5FA',
                borderRadius: '50%',
                animation: 'spin 0.9s linear infinite',
              }} />
              <div style={{
                color: '#E2E8F0', fontSize: '14px', fontWeight: 600,
                letterSpacing: '0.05em', textTransform: 'uppercase',
              }}>
                Recomputing Geometry...
              </div>
              <div style={{ color: '#94A3B8', fontSize: '11px' }}>
                Complex boolean ops may take 30–60s
              </div>
            </div>
          )}
        </div>


        {/* AutoCAD Bottom Status Bar & Precision Coordinate Tracker */}
        <div className="autocad-statusbar">
          <div className="autocad-coords">
            <span className="coord-axis">X:</span> {cursorCoords.x} &nbsp;
            <span className="coord-axis">Y:</span> {cursorCoords.y} &nbsp;
            <span className="coord-axis">Z:</span> {cursorCoords.z}
          </div>
          <div className="autocad-status-chips">
            <span className="autocad-chip active">MODEL</span>
            <button
              className={`autocad-chip ${showGrid ? 'active' : ''}`}
              onClick={() => setShowGrid(!showGrid)}
              title="Toggle AutoCAD Construction Grid (F7)"
            >
              GRID
            </button>
            <button
              className={`autocad-chip ${showAxes ? 'active' : ''}`}
              onClick={() => setShowAxes(!showAxes)}
              title="Toggle AutoCAD UCS Coordinate Icon"
            >
              UCS
            </button>
            <button
              className={`autocad-chip ${showDimensions ? 'active' : ''}`}
              onClick={() => setShowDimensions(!showDimensions)}
              title="Toggle 3D Bounding Dimensions"
            >
              DIMS
            </button>
            <button
              className={`autocad-chip ${visualStyle === 'shaded_edges' ? 'active' : ''}`}
              onClick={() => setVisualStyle(visualStyle === 'shaded_edges' ? 'realistic' : 'shaded_edges')}
              title="Toggle Shaded Feature Edges"
            >
              EDGES
            </button>
            <span className="autocad-chip active">ORTHO</span>
            <span className="autocad-chip active">OSNAP</span>
            <span className="autocad-chip active">3D OSNAP</span>
          </div>
        </div>

        {/* Empty Canvas Placeholder */}
        {!meshUrl && !loading && (
          <div className="viewer-empty">
            <div className="viewer-empty-card">
              <div className="viewer-empty-icon">
                <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                  <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
                  <line x1="12" y1="22.08" x2="12" y2="12"/>
                </svg>
              </div>
              <div className="viewer-empty-title">The CAD Atelier Studio</div>
              <div className="viewer-empty-sub">
                Compose a mechanical description on the left or select an atelier preset.
                The workbench synthesizes real OpenCASCADE boundary-representation solid geometry via <code>build123d</code>.
              </div>
              <div className="empty-features-grid">
                <div className="empty-feature-item">
                  <span className="empty-feature-bullet" />
                  <span>Shaded with Visible Edges</span>
                </div>
                <div className="empty-feature-item">
                  <span className="empty-feature-bullet" />
                  <span>Interactive 3D ViewCube</span>
                </div>
                <div className="empty-feature-item">
                  <span className="empty-feature-bullet" />
                  <span>Sub-200ms Slider Recompute</span>
                </div>
                <div className="empty-feature-item">
                  <span className="empty-feature-bullet" />
                  <span>STEP & STL Dual Export</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Generation Loading Overlay */}
        {loading && (
          <div className="loading-overlay">
            <div className="loading-card">
              <div className="spinner loading-spinner-large" />
              <div className="loading-title">Synthesizing Solid B-Rep Geometry...</div>
              <div className="loading-sub">
                ChromaDB k-NN Retrieval ➔ LLM Code Synthesis ➔ Subprocess AST Execution ➔ Manifold Validation
              </div>
            </div>
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <div className="error-banner">
            <span className="error-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            </span>
            <div className="error-msg">{error}</div>
            <button className="error-dismiss" onClick={() => setError(null)}>✕</button>
          </div>
        )}

        {/* Python CAD Script Code Inspector Modal */}
        {showCodeModal && pythonCode && (
          <div className="modal-backdrop" onClick={() => setShowCodeModal(false)}>
            <div
              className="modal-card"
              role="dialog"
              aria-modal="true"
              aria-labelledby="code-modal-title"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <div className="modal-title-group">
                  <span className="modal-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="16 18 22 12 16 6"/>
                      <polyline points="8 6 2 12 8 18"/>
                    </svg>
                  </span>
                  <div>
                    <div className="modal-title" id="code-modal-title">build123d Python Script ({scriptId})</div>
                    <div className="modal-subtitle">Runtime build123d script with injected export paths</div>
                  </div>
                </div>
                <button
                  className="modal-close-btn"
                  onClick={() => setShowCodeModal(false)}
                  aria-label="Close code inspector"
                  autoFocus
                >✕</button>
              </div>

              <pre className="modal-code"><code>{pythonCode}</code></pre>

              <div className="modal-footer">
                <span className="modal-hint">All parameters are exposed in the PARAMS dict at the top of the script.</span>
                <div className="modal-actions">
                  <button
                    className="toolbar-btn export-btn"
                    onClick={async () => {
                      try {
                        if (!navigator.clipboard) throw new Error('Clipboard unavailable');
                        await navigator.clipboard.writeText(pythonCode);
                        alert('Python CAD code copied to clipboard!');
                      } catch {
                        setError('Clipboard access was denied. Select and copy the code manually.');
                      }
                    }}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
                  >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                    </svg>
                    <span>Copy Code</span>
                  </button>
                  <button className="toolbar-btn" onClick={() => setShowCodeModal(false)}>
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
