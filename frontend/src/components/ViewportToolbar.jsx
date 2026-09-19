import React from 'react';

/**
 * ViewportToolbar — Controls 3D view mode, camera angle, material finish, background environment, and export dropdown.
 */
export default function ViewportToolbar({
  visualStyle,
  setVisualStyle,
  VISUAL_STYLES,
  activeCamView,
  handleCameraPreset,
  viewerRef,
  materialType,
  setMaterialType,
  MATERIAL_PRESETS,
  backgroundTheme,
  setBackgroundTheme,
  VIEWPORT_BACKGROUNDS,
  meshUrl,
  stepUrl,
  objUrl,
  glbUrl,
  pythonCode,
  partName,
  openDropdown,
  setOpenDropdown,
  toggleDropdown,
  fileUrl,
  setShowCodeModal,
  toolbarRef,
}) {
  // Compact display labels to avoid navbar congestion
  const displayStyleName = (VISUAL_STYLES[visualStyle]?.name || 'Shaded').replace(' with Edges', '');
  const displayCamName = activeCamView === 'iso' ? 'Iso' : activeCamView.toUpperCase();
  const displayMatName = (MATERIAL_PRESETS[materialType]?.name || 'Finish').replace('Standard ', '');

  return (
    <div className="header-nav-dropdowns" ref={toolbarRef}>
      {/* Segmented Viewport Controls: Style | Cam | Material */}
      <div className="vt-segmented-group">
        {/* Visual Style Dropdown */}
        <div className="vt-dropdown">
          <button
            type="button"
            className={`vt-dropdown-trigger ${openDropdown === 'style' ? 'open' : ''}`}
            onClick={() => toggleDropdown('style')}
            title="Display Style (Shaded / Wireframe / Edges)"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="12 2 2 7 12 12 22 7 12 2"/>
              <polyline points="2 17 12 22 22 17"/>
              <polyline points="2 12 12 17 22 12"/>
            </svg>
            <span>{displayStyleName}</span>
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

        <div className="vt-divider" />

        {/* Camera View Dropdown */}
        <div className="vt-dropdown">
          <button
            type="button"
            className={`vt-dropdown-trigger ${openDropdown === 'view' ? 'open' : ''}`}
            onClick={() => toggleDropdown('view')}
            title="Camera Angle (Isometric / Top / Front / Side)"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
              <circle cx="12" cy="13" r="4"/>
            </svg>
            <span>{displayCamName}</span>
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

        <div className="vt-divider" />

        {/* Surface Finish / Material Dropdown */}
        <div className="vt-dropdown">
          <button
            type="button"
            className={`vt-dropdown-trigger ${openDropdown === 'material' ? 'open' : ''}`}
            onClick={() => toggleDropdown('material')}
            title="Surface Material & Canvas Finish"
          >
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: MATERIAL_PRESETS[materialType]?.swatch || '#CBD5E1', display: 'inline-block' }} />
            <span>{displayMatName}</span>
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
      </div>

      {/* Export Dropdown */}
      <div className="vt-dropdown">
        <button
          type="button"
          className={`vt-dropdown-trigger vt-export-trigger ${openDropdown === 'export' ? 'open' : ''}`}
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
            <div className="vt-dropdown-label">3D Formats</div>
            {meshUrl ? (
              <a
                href={fileUrl(meshUrl)}
                download={`${partName || 'part'}.stl`}
                className="vt-dropdown-item"
                onClick={() => setOpenDropdown(null)}
              >
                <span className="item-dot active" />
                <span>STL Mesh <span style={{ opacity: 0.5, fontSize: '10px' }}>WebGL preview</span></span>
              </a>
            ) : (
              <div className="vt-dropdown-item" style={{ opacity: 0.5, cursor: 'not-allowed' }}>
                <span className="item-dot" />
                <span>STL Mesh (generate first)</span>
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
                <span>STEP B-Rep <span style={{ opacity: 0.5, fontSize: '10px' }}>CAD/CAM</span></span>
              </a>
            ) : (
              <div className="vt-dropdown-item" style={{ opacity: 0.5, cursor: 'not-allowed' }}>
                <span className="item-dot" />
                <span>STEP B-Rep (generate first)</span>
              </div>
            )}
            {objUrl ? (
              <a
                href={fileUrl(objUrl)}
                download={`${partName || 'part'}.obj`}
                className="vt-dropdown-item"
                onClick={() => setOpenDropdown(null)}
              >
                <span className="item-dot active" />
                <span>Wavefront OBJ <span style={{ opacity: 0.5, fontSize: '10px' }}>game engines</span></span>
              </a>
            ) : (
              <div className="vt-dropdown-item" style={{ opacity: 0.5, cursor: 'not-allowed' }}>
                <span className="item-dot" />
                <span>OBJ (generate first)</span>
              </div>
            )}
            {glbUrl ? (
              <a
                href={fileUrl(glbUrl)}
                download={`${partName || 'part'}.glb`}
                className="vt-dropdown-item"
                onClick={() => setOpenDropdown(null)}
              >
                <span className="item-dot active" />
                <span>GLB Binary GLTF <span style={{ opacity: 0.5, fontSize: '10px' }}>WebGL / AR</span></span>
              </a>
            ) : (
              <div className="vt-dropdown-item" style={{ opacity: 0.5, cursor: 'not-allowed' }}>
                <span className="item-dot" />
                <span>GLB / glTF (generate first)</span>
              </div>
            )}
            <div className="vt-dropdown-label" style={{ marginTop: '8px' }}>Source</div>
            {pythonCode && (
              <button
                type="button"
                className="vt-dropdown-item"
                onClick={() => { setShowCodeModal(true); setOpenDropdown(null); }}
              >
                <span className="item-dot active" />
                <span>Python CAD Script <span style={{ opacity: 0.5, fontSize: '10px' }}>.py</span></span>
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
