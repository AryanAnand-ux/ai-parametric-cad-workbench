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
import AuthModal from './components/AuthModal';
import ProjectSidebar from './components/ProjectSidebar';
import GenerationProgress from './components/GenerationProgress';
import OnboardingTour from './components/OnboardingTour';
import ShareModal from './components/ShareModal';
import ErrorBanner from './components/ErrorBanner';
import TelemetryHUD from './components/TelemetryHUD';
import ViewportToolbar from './components/ViewportToolbar';
import PromptPanel from './components/PromptPanel';
import ChatModifyPanel from './components/ChatModifyPanel';
import CodeInspectorModal from './components/CodeInspectorModal';
import { useAuth } from './hooks/useAuth';
import { useCADWorkbench } from './hooks/useCADWorkbench';
import {
  generatePart,
  generatePartStream,
  recomputePart,
  healthCheck,
  modifyPart,
  resolveAssetUrl,
  getGenerationDetail,
} from './api';
import { VISUAL_STYLES, VIEWPORT_BACKGROUNDS } from './constants/visualStyles';

// Build a full URL for file downloads / static assets
const fileUrl = (path) => {
  return resolveAssetUrl(path);
};

// Categorized Preset CAD Prompts — 8 Universal Archetypes
const PRESET_CATEGORIES = [
  {
    category: 'Engineering & Thermal',
    prompts: [
      { label: 'CPU Heatsink', prompt: 'High-performance linear extruded aluminum CPU heatsink with rectangular fin array, thick heat spreader base plate, and 4 corner mounting screw holes' },
      { label: 'Radial Heatsink', prompt: 'Cylindrical radial heatsink with solid inner core, 12 radial cooling fins, and center mounting bore' },
      { label: 'Weld Neck Flange', prompt: 'Class 150 weld neck pipe flange with raised face, through bore, tapered welding neck hub, and 8-bolt circle pattern' },
      { label: 'V-Belt Pulley', prompt: 'Single-groove industrial V-belt drive pulley with central hub, shaft bore, keyway slot, web plate, and 38-degree trapezoidal V-groove rim' }
    ]
  },
  {
    category: 'Transmission & Powertrain',
    prompts: [
      { label: 'Spur Gear Blank', prompt: 'Machined industrial spur gear blank with central hub, shaft bore, standard keyway, recessed web, and outer rim with circular lightening holes' },
      { label: 'Stepped Drive Shaft', prompt: 'Three-step mechanical transmission drive shaft with precision bearing journals, central gear seating shoulder, keyway, and retaining circlip groove' },
      { label: 'Spider Coupling', prompt: 'Three-jaw flexible spider shaft coupling hub with central bore, keyway, clamping slit, and interlocking curved drive jaws' },
      { label: 'Drive Sprocket', prompt: 'Roller chain drive sprocket blank with central keyed bore and outer toothed rim' }
    ]
  },
  {
    category: 'Vessels & Ducts',
    prompts: [
      { label: 'Coffee Mug', prompt: 'Ceramic style coffee mug with cylindrical body, hollow cavity, smooth rim fillet, and curved ergonomic sweep handle' },
      { label: 'Swept 90° Elbow', prompt: '90 degree smooth swept pipe elbow duct with circular cross section, swept along circular arc path with bolted flanged ends' },
      { label: 'Pressure Canister', prompt: 'Cylindrical pressure vessel canister with domed hemispherical top, thick base, and NPT threaded central port boss' }
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
    category: 'Enclosures & Brackets',
    prompts: [
      { label: 'Enclosure Box', prompt: 'Rectangular electronics project box bottom enclosure with rounded corners, hollow interior, 4 corner PCB screw standoff bosses, and side cable gland cutout' },
      { label: 'Mounting Bracket', prompt: 'A mounting bracket with four M5 corner holes, 80x50x5mm with 4mm fillets' },
      { label: 'Hydraulic Manifold', prompt: 'High-pressure hydraulic valve subplate manifold block with standard P, T, A, B port counterbores, internal galleries, and mounting holes' }
    ]
  }
];

const QUICK_MODIFICATIONS = [
  'Make walls 2mm thicker',
  'Add 4x M3 corner mounting holes',
  'Add 3mm fillets to all vertical edges',
  'Increase overall length by 20mm',
  'Add central 15mm bore hole',
  'Hollow out interior with 3mm shell'
];

export default function App({ onGoHome, onGoToGallery }) {
  const {
    state,
    paramValuesRef,
    setField,
    setError,
    dismissError,
    applyPartResponse,
    setRecomputeSuccess,
    resetParams,
    pushSnapshot,
    popSnapshot,
    setPrompt,
    setActiveTab,
    setParameterSearch,
    setModifyPrompt,
    setModifying,
    setLoading,
    setRecomputing,
    setVisualStyle,
    setMaterialType,
    setBackgroundTheme,
    setShowAxes,
    setShowGrid,
    setShowDimensions,
    setCursorCoords,
    setActiveCamView,
    setShowCodeModal,
    setShowAuthModal,
    setShowProjectSidebar,
    setShowShareModal,
    setShowOnboarding,
    setBackendStatus,
    setChatHistory,
    updateParamValue,
    updateStream,
  } = useCADWorkbench();

  const {
    prompt,
    loading,
    recomputing,
    error,
    scriptId,
    partName,
    description,
    pythonCode,
    parameters,
    parameterSearch,
    paramValues,
    meshUrl,
    stepUrl,
    objUrl,
    glbUrl,
    meshInfo,
    recompTime,
    modelUsed,
    designMode,
    components,
    backendStatus,
    activeTab,
    chatHistory,
    modifyPrompt,
    modifying,
    modelHistory,
    showAxes,
    showGrid,
    materialType,
    visualStyle,
    backgroundTheme,
    cursorCoords,
    activeCamView,
    showDimensions,
    showCodeModal,
    showAuthModal,
    showProjectSidebar,
    showShareModal,
    showOnboarding,
    streamPhase,
    streamProgress,
    streamMessage,
    streamAttempts,
  } = state;

  const viewerRef = useRef(null);
  const chatEndRef = useRef(null);
  const { user, isAuthenticated, login, register, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [openDropdown, setOpenDropdown] = useState(null);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const dropdownRef = useRef(null);
  const userMenuRef = useRef(null);
  const debounceTimerRef = useRef(null);
  const scrollTimerRef = useRef(null);
  const recomputeSequenceRef = useRef(0);

  // Health check on mount + debounce timer cleanup + tour persistence
  useEffect(() => {
    healthCheck()
      .then((data) => setBackendStatus(data.status === 'online' ? 'online' : 'offline'))
      .catch(() => setBackendStatus('offline'));

    // Don't auto-show tour if user already completed it
    if (localStorage.getItem('cad_tour_completed') === '1') {
      setShowOnboarding(false);
    }

    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
      if (scrollTimerRef.current) clearTimeout(scrollTimerRef.current);
    };
  }, [setBackendStatus, setShowOnboarding]);

  // Close dropdown on outside click
  useEffect(() => {
    if (!openDropdown && !userMenuOpen) return undefined;
    const handle = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpenDropdown(null);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, [openDropdown, userMenuOpen]);

  const toggleDropdown = (key) => setOpenDropdown((prev) => (prev === key ? null : key));

  useEffect(() => {
    if (!showCodeModal) return undefined;
    const handleEscape = (event) => {
      if (event.key === 'Escape') setShowCodeModal(false);
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [showCodeModal, setShowCodeModal]);


  // Submit prompt -> /api/generate/stream with fallback to /api/generate
  const handleGenerate = async (overridePrompt) => {
    const activePrompt = overridePrompt || prompt;
    if (!activePrompt.trim() || loading) return;

    setLoading(true);
    setError(null);
    setChatHistory([]);
    updateStream({
      phase: 'rag_retrieval',
      progress: 12,
      message: 'Vector search across 121 CAD blueprints...',
      attempts: 0,
    });

    try {
      const res = await generatePartStream(activePrompt, (evt) => {
        updateStream({
          phase: evt.phase,
          progress: evt.progress,
          message: evt.message,
          attempts: evt.phase === 'self_correction' ? (streamAttempts + 1) : streamAttempts,
        });
      });
      applyPartResponse(res);
    } catch (streamErr) {
      console.warn('[SSE stream fallback to standard POST]', streamErr);
      try {
        const res = await generatePart(activePrompt);
        applyPartResponse(res);
      } catch (err) {
        console.error('[Generate error]', err);
        const detail = err.response?.data?.detail;
        setError(typeof detail === 'string' ? detail : (detail?.error || err.message || streamErr.message || 'Generation failed. Check backend log.'));
      }
    } finally {
      setLoading(false);
    }
  };

  // Select and load a saved generation from the workspace drawer
  const handleSelectGeneration = async (genId) => {
    try {
      setLoading(true);
      updateStream({
        phase: 'cad_execution',
        progress: 60,
        message: 'Restoring saved workspace design...',
      });
      const gen = await getGenerationDetail(genId);
      applyPartResponse({
        script_id: gen.script_id,
        part_name: gen.part_name,
        description: gen.description,
        python_code: gen.python_code,
        parameters: gen.parameters || [],
        mesh_url: gen.mesh_url,
        step_url: gen.step_url,
        obj_url: gen.obj_url,
        glb_url: gen.glb_url,
        mesh_info: gen.mesh_info || {},
        recomputation_time_ms: gen.generation_time_ms,
        model_used: gen.model_used,
        design_mode: gen.design_mode || 'single_solid',
        components: gen.components || null,
      });
      setShowProjectSidebar(false);
    } catch (err) {
      console.error('Failed to load saved model:', err);
      setError('Could not load saved model.');
    } finally {
      setLoading(false);
    }
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
      pushSnapshot();
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
      if (scrollTimerRef.current) clearTimeout(scrollTimerRef.current);
      scrollTimerRef.current = setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    }
  };

  // Slider change -> fast /api/recompute (<200ms)
  const handleParamChange = useCallback((name, value) => {
    const requestSequence = ++recomputeSequenceRef.current;
    paramValuesRef.current = { ...paramValuesRef.current, [name]: value };
    updateParamValue(name, value);

    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);

    debounceTimerRef.current = setTimeout(async () => {
      if (!scriptId || !pythonCode) return;
      setRecomputing(true);

      try {
        const res = await recomputePart(
          scriptId,
          pythonCode,
          paramValuesRef.current,
          parameters,
          designMode,
          components,
        );
        if (requestSequence !== recomputeSequenceRef.current) return;
        setRecomputeSuccess(res);
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
  }, [parameters, scriptId, pythonCode, designMode, components, setRecomputing, setRecomputeSuccess, setError, updateParamValue]);

  // Reset all sliders to defaults AND trigger recompute on canvas
  const handleResetAll = async () => {
    if (!parameters.length || !scriptId || !pythonCode) return;
    const resetVals = {};
    parameters.forEach((p) => { resetVals[p.name] = p.default; });
    const requestSequence = ++recomputeSequenceRef.current;
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    paramValuesRef.current = resetVals;
    resetParams();
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
      setRecomputeSuccess(res);
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

  // Recompute with current slider values immediately (Shortcut: R)
  const handleForceRecompute = async () => {
    if (!scriptId || !pythonCode || recomputing) return;
    const requestSequence = ++recomputeSequenceRef.current;
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    setRecomputing(true);
    try {
      const res = await recomputePart(
        scriptId,
        pythonCode,
        paramValuesRef.current,
        parameters,
        designMode,
        components,
      );
      if (requestSequence !== recomputeSequenceRef.current) return;
      setRecomputeSuccess(res);
    } catch (err) {
      if (requestSequence !== recomputeSequenceRef.current) return;
      console.error('[Force recompute error]', err);
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : (detail?.error || err.message || 'Recomputation failed.');
      setError(`Recomputation error: ${msg}`);
    } finally {
      if (requestSequence === recomputeSequenceRef.current) setRecomputing(false);
    }
  };

  const handleCameraPreset = (view) => {
    setActiveCamView(view);
    viewerRef.current?.setCameraView(view);
  };

  // Global keyboard shortcuts — only fire when no input/textarea/select is focused
  useEffect(() => {
    const handleKey = (e) => {
      const tag = document.activeElement?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      switch (e.key) {
        case 'g': case 'G':
          e.preventDefault();
          handleGenerate();
          break;
        case 'r': case 'R':
          if (scriptId && pythonCode && !recomputing) {
            e.preventDefault();
            handleForceRecompute();
          }
          break;
        case 'e': case 'E':
          if (meshUrl) {
            e.preventDefault();
            toggleDropdown('export');
          }
          break;
        case '?':
          e.preventDefault();
          setShowOnboarding(true);
          break;
        case 'z': case 'Z':
          if (modelHistory.length > 0) {
            e.preventDefault();
            popSnapshot();
          }
          break;
        default:
          break;
      }
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [scriptId, pythonCode, recomputing, meshUrl, modelHistory, handleGenerate, handleForceRecompute, popSnapshot, setShowOnboarding]);

  return (
    <div className={`app-shell${sidebarOpen ? '' : ' sidebar-collapsed'}`}>
      {/* ── BENTO HEADER ─────────────────────────────────────────── */}
      <header className="header">
        <div className="header-logo">
          <button
            className="sidebar-toggle-btn"
            onClick={() => setSidebarOpen((v) => !v)}
            title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
            aria-label="Toggle sidebar"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              {sidebarOpen ? <polyline points="15 18 9 12 15 6" /> : <polyline points="9 18 15 12 9 6" />}
            </svg>
          </button>
          <div
            className="header-brand-link"
            onClick={() => {
              if (onGoHome) onGoHome();
              else window.location.hash = '';
            }}
            title="Return to Landing Page"
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                if (onGoHome) onGoHome();
                else window.location.hash = '';
              }
            }}
          >
            <div className="header-logo-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
                <line x1="12" y1="22.08" x2="12" y2="12"/>
              </svg>
            </div>
            <div className="header-brand-info">
              <span className="header-title">The CAD Atelier</span>
              <span className="header-badge-tag">v2.0</span>
            </div>
          </div>
        </div>

        {/* ── NAVBAR CAD OPTIONS DROPDOWNS ── */}
        <ViewportToolbar
          visualStyle={visualStyle}
          setVisualStyle={setVisualStyle}
          VISUAL_STYLES={VISUAL_STYLES}
          activeCamView={activeCamView}
          handleCameraPreset={handleCameraPreset}
          viewerRef={viewerRef}
          materialType={materialType}
          setMaterialType={setMaterialType}
          MATERIAL_PRESETS={MATERIAL_PRESETS}
          backgroundTheme={backgroundTheme}
          setBackgroundTheme={setBackgroundTheme}
          VIEWPORT_BACKGROUNDS={VIEWPORT_BACKGROUNDS}
          meshUrl={meshUrl}
          stepUrl={stepUrl}
          objUrl={objUrl}
          glbUrl={glbUrl}
          pythonCode={pythonCode}
          partName={partName}
          openDropdown={openDropdown}
          setOpenDropdown={setOpenDropdown}
          toggleDropdown={toggleDropdown}
          fileUrl={fileUrl}
          setShowCodeModal={setShowCodeModal}
          toolbarRef={dropdownRef}
        />

        <div className="header-actions">
          {/* Quick Undo if history available */}
          {modelHistory.length > 0 && (
            <button
              className="toolbar-btn header-action-btn header-btn-undo"
              onClick={popSnapshot}
              title={`Undo to previous state (${modelHistory.length} in stack)`}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 10h10a5 5 0 0 1 5 5v2"/>
                <polyline points="7 6 3 10 7 14"/>
              </svg>
              <span>Undo</span>
              <span className="header-btn-badge">{modelHistory.length}</span>
            </button>
          )}

          {/* Inspect Python Code */}
          {pythonCode && (
            <button
              className="toolbar-btn header-action-btn header-icon-btn"
              onClick={() => setShowCodeModal(true)}
              title="Inspect Python CAD Script (build123d)"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="16 18 22 12 16 6"/>
                <polyline points="8 6 2 12 8 18"/>
              </svg>
              <span className="header-btn-text">Code</span>
            </button>
          )}

          {/* Share Design Modal Trigger */}
          {scriptId && (
            <button
              className="toolbar-btn header-action-btn"
              onClick={() => setShowShareModal(true)}
              title="Share CAD Model or Copy 3D Embed"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
                <polyline points="16 6 12 2 8 6"/>
                <line x1="12" y1="2" x2="12" y2="15"/>
              </svg>
              <span>Share</span>
            </button>
          )}

          <div className="header-divider" />

          {/* Workspaces Drawer */}
          <button
            className="toolbar-btn header-action-btn"
            onClick={() => {
              if (!isAuthenticated) {
                setShowAuthModal(true);
              } else {
                setShowProjectSidebar(true);
              }
            }}
            title="Open Workspaces & Saved Designs"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            </svg>
            <span className="header-btn-text">Workspaces</span>
          </button>

          {/* Guided Tour Trigger (clean icon button) */}
          <button
            className="toolbar-btn header-action-btn header-icon-only-btn"
            onClick={() => setShowOnboarding(true)}
            title="Interactive Studio Tour"
          >
            <span>💡</span>
          </button>

          <div className="header-divider" />

          {/* CAD Engine Status Indicator (compact pill) */}
          <div
            className="header-status-indicator"
            title={`CAD Engine: ${backendStatus === 'online' ? 'Online & Operational' : backendStatus === 'offline' ? 'Offline' : 'Connecting'}`}
          >
            <span
              className="status-dot"
              style={{ background: backendStatus === 'online' ? '#489235' : '#EF4444' }}
            />
            <span className="status-label">{backendStatus === 'online' ? 'Ready' : 'Connecting'}</span>
          </div>

          {/* Auth State Button / Profile Dropdown Menu */}
          {isAuthenticated ? (
            <div className="vt-dropdown" ref={userMenuRef}>
              <button
                className="toolbar-btn header-action-btn user-profile-btn"
                onClick={() => setUserMenuOpen((v) => !v)}
                title={`Signed in as ${user?.email}`}
              >
                <span className="user-avatar-dot">
                  {(user?.display_name || user?.email || 'U').charAt(0).toUpperCase()}
                </span>
                <span className="user-name-label">{user?.display_name || user?.email?.split('@')[0]}</span>
                <span className="user-plan-badge">{user?.plan_tier || 'PRO'}</span>
                <span className="chevron">▼</span>
              </button>
              {userMenuOpen && (
                <div className="vt-dropdown-menu user-dropdown-menu">
                  <div className="user-menu-header">
                    <div className="user-menu-name">{user?.display_name || 'CAD Designer'}</div>
                    <div className="user-menu-email">{user?.email}</div>
                  </div>
                  <div className="vt-dropdown-sep" />
                  <button
                    type="button"
                    className="vt-dropdown-item"
                    onClick={() => { setShowProjectSidebar(true); setUserMenuOpen(false); }}
                  >
                    <span>📁 Saved Projects</span>
                  </button>
                  <button
                    type="button"
                    className="vt-dropdown-item"
                    onClick={() => {
                      localStorage.removeItem('cad_tour_completed');
                      setShowOnboarding(true);
                      setUserMenuOpen(false);
                    }}
                  >
                    <span>💡 Reset Tour</span>
                  </button>
                  <div className="vt-dropdown-sep" />
                  <button
                    type="button"
                    className="vt-dropdown-item text-danger"
                    onClick={() => { logout(); setUserMenuOpen(false); }}
                  >
                    <span>Sign Out</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <button
              className="toolbar-btn header-action-btn sign-in-btn"
              onClick={() => setShowAuthModal(true)}
            >
              Sign In
            </button>
          )}
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
          <PromptPanel
            prompt={prompt}
            setPrompt={setPrompt}
            loading={loading}
            handleGenerate={handleGenerate}
            PRESET_CATEGORIES={PRESET_CATEGORIES}
          />
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
                <TelemetryHUD
                  meshInfo={meshInfo}
                  recompTime={recompTime}
                  modelUsed={modelUsed}
                  designMode={designMode}
                />
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
        <ChatModifyPanel
          scriptId={scriptId}
          activeTab={activeTab}
          chatHistory={chatHistory}
          chatEndRef={chatEndRef}
          modifyPrompt={modifyPrompt}
          setModifyPrompt={setModifyPrompt}
          modifying={modifying}
          handleModify={handleModify}
          QUICK_MODIFICATIONS={QUICK_MODIFICATIONS}
        />
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

        {/* Generation Real-Time Pipeline Progress Overlay */}
        {loading && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              zIndex: 100,
              backgroundColor: 'rgba(5, 7, 15, 0.85)',
              backdropFilter: 'blur(8px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '24px',
            }}
          >
            <GenerationProgress
              currentPhase={streamPhase}
              progress={streamProgress}
              message={streamMessage}
              attempts={streamAttempts}
            />
          </div>
        )}

        {/* Error Banner */}
        <ErrorBanner error={error} onDismiss={dismissError} />

        {/* Python CAD Script Code Inspector Modal */}
        <CodeInspectorModal
          isOpen={showCodeModal}
          onClose={() => setShowCodeModal(false)}
          pythonCode={pythonCode}
          partName={partName}
          scriptId={scriptId}
          onError={setError}
        />
      </main>

      {/* User Authentication Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onLogin={login}
        onRegister={register}
      />

      {/* Projects & Workspaces Drawer */}
      <ProjectSidebar
        isOpen={showProjectSidebar}
        onClose={() => setShowProjectSidebar(false)}
        onSelectGeneration={handleSelectGeneration}
        currentScriptId={scriptId}
      />

      {/* Guided Onboarding Walkthrough */}
      <OnboardingTour
        isOpen={showOnboarding}
        onClose={() => {
          setShowOnboarding(false);
          try {
            localStorage.setItem('cad_onboarding_completed', 'true');
          } catch {
            // ignore
          }
        }}
      />

      {/* Share & Embed Modal */}
      <ShareModal
        isOpen={showShareModal}
        onClose={() => setShowShareModal(false)}
        scriptId={scriptId}
        partName={partName}
        meshUrl={meshUrl ? fileUrl(meshUrl) : null}
        stepUrl={stepUrl ? fileUrl(stepUrl) : null}
      />
    </div>
  );
}
