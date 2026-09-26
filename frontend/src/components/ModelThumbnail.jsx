import React from 'react';

/**
 * ModelThumbnail — Precision Engineering CAD Isometric Preview
 * 
 * Renders an archetype-specific vector CAD blueprint thumbnail with:
 * - Technical coordinate grid backdrop & tick marks
 * - Archetype geometry representation (Gear, Bracket, Enclosure, Shaft, Stand, Heatsink, Flange, Duct, or Generic)
 * - Dimension callouts and technical badges
 */

function detectArchetype(item) {
  const name = (item.part_name || '').toLowerCase();
  const tags = (item.tags || []).map(t => String(t).toLowerCase());
  const allText = `${name} ${tags.join(' ')}`;

  if (allText.includes('gear') || allText.includes('sprocket')) return 'gear';
  if (allText.includes('bracket') || allText.includes('gusset') || allText.includes('mount')) return 'bracket';
  if (allText.includes('enclosure') || allText.includes('box') || allText.includes('shell') || allText.includes('case')) return 'enclosure';
  if (allText.includes('shaft') || allText.includes('cylinder') || allText.includes('lathe') || allText.includes('journal')) return 'shaft';
  if (allText.includes('stand') || allText.includes('holder') || allText.includes('cradle')) return 'stand';
  if (allText.includes('heatsink') || allText.includes('fin') || allText.includes('cooler')) return 'heatsink';
  if (allText.includes('flange') || allText.includes('pipe') || allText.includes('valve')) return 'flange';
  if (allText.includes('elbow') || allText.includes('duct') || allText.includes('nozzle') || allText.includes('vessel')) return 'duct';
  return 'generic';
}

function ArchetypeGeometry({ type }) {
  switch (type) {
    case 'gear':
      return (
        <svg viewBox="0 0 120 120" width="100%" height="100%" style={{ overflow: 'visible' }}>
          {/* Pitch circle */}
          <circle cx="60" cy="60" r="44" fill="none" stroke="#B0A9A8" strokeWidth="1" strokeDasharray="3 3" />
          {/* Root circle */}
          <circle cx="60" cy="60" r="34" fill="#E8E8DE" stroke="#5E5656" strokeWidth="1.5" />
          {/* Lightening holes */}
          <circle cx="60" cy="42" r="5" fill="#FAF9F5" stroke="#7A7272" strokeWidth="1.2" />
          <circle cx="78" cy="60" r="5" fill="#FAF9F5" stroke="#7A7272" strokeWidth="1.2" />
          <circle cx="60" cy="78" r="5" fill="#FAF9F5" stroke="#7A7272" strokeWidth="1.2" />
          <circle cx="42" cy="60" r="5" fill="#FAF9F5" stroke="#7A7272" strokeWidth="1.2" />
          {/* Shaft bore with keyway */}
          <circle cx="60" cy="60" r="12" fill="#FAF9F5" stroke="#474040" strokeWidth="1.8" />
          <rect x="58" y="45" width="4" height="6" fill="#FAF9F5" stroke="#474040" strokeWidth="1.5" />
          {/* Gear teeth */}
          {[...Array(16)].map((_, i) => {
            const angle = (i * 360) / 16;
            return (
              <g key={i} transform={`rotate(${angle} 60 60)`}>
                <polygon points="56,16 64,16 66,26 54,26" fill="#D3D1C4" stroke="#474040" strokeWidth="1.2" />
              </g>
            );
          })}
          {/* Center crosshair */}
          <line x1="60" y1="52" x2="60" y2="68" stroke="#8A8282" strokeWidth="0.8" strokeDasharray="2 2" />
          <line x1="52" y1="60" x2="68" y2="60" stroke="#8A8282" strokeWidth="0.8" strokeDasharray="2 2" />
        </svg>
      );

    case 'bracket':
      return (
        <svg viewBox="0 0 120 120" width="100%" height="100%" style={{ overflow: 'visible' }}>
          {/* L-Bracket isometric perspective */}
          {/* Vertical leg */}
          <polygon points="32,24 50,14 50,86 32,96" fill="#DDD9CE" stroke="#474040" strokeWidth="1.6" />
          <polygon points="50,14 62,21 62,93 50,86" fill="#BBB5A8" stroke="#474040" strokeWidth="1.6" />
          {/* Horizontal leg */}
          <polygon points="32,96 50,86 98,86 80,96" fill="#E8E5DD" stroke="#474040" strokeWidth="1.6" />
          <polygon points="80,96 98,86 98,92 80,102" fill="#BBB5A8" stroke="#474040" strokeWidth="1.6" />
          {/* Gusset triangle rib */}
          <polygon points="50,42 50,86 82,86" fill="#C9C3B5" stroke="#474040" strokeWidth="1.4" />
          {/* Mounting holes */}
          <ellipse cx="41" cy="40" rx="3.5" ry="4.5" fill="#FAF9F5" stroke="#474040" strokeWidth="1.2" />
          <ellipse cx="41" cy="68" rx="3.5" ry="4.5" fill="#FAF9F5" stroke="#474040" strokeWidth="1.2" />
          <ellipse cx="70" cy="91" rx="4.5" ry="2.5" fill="#FAF9F5" stroke="#474040" strokeWidth="1.2" />
        </svg>
      );

    case 'enclosure':
      return (
        <svg viewBox="0 0 120 120" width="100%" height="100%" style={{ overflow: 'visible' }}>
          {/* Isometric box enclosure */}
          <polygon points="60,22 96,42 96,78 60,98 24,78 24,42" fill="#E5E1D5" stroke="#474040" strokeWidth="1.6" />
          {/* Inner cavity */}
          <polygon points="60,34 86,49 86,72 60,87 34,72 34,49" fill="#D3CEBF" stroke="#474040" strokeWidth="1.4" />
          {/* Corner bosses */}
          <circle cx="38" cy="52" r="3" fill="#E5E1D5" stroke="#474040" strokeWidth="1.2" />
          <circle cx="82" cy="52" r="3" fill="#E5E1D5" stroke="#474040" strokeWidth="1.2" />
          <circle cx="38" cy="69" r="3" fill="#E5E1D5" stroke="#474040" strokeWidth="1.2" />
          <circle cx="82" cy="69" r="3" fill="#E5E1D5" stroke="#474040" strokeWidth="1.2" />
          {/* Side cutout */}
          <polygon points="96,52 96,62 90,65 90,55" fill="#474040" />
        </svg>
      );

    case 'shaft':
      return (
        <svg viewBox="0 0 120 120" width="100%" height="100%" style={{ overflow: 'visible' }}>
          {/* Stepped shaft 3 sections */}
          <rect x="18" y="52" width="22" height="16" fill="#DDD9CF" stroke="#474040" strokeWidth="1.5" />
          <rect x="40" y="44" width="42" height="32" fill="#E8E5DC" stroke="#474040" strokeWidth="1.6" />
          <rect x="82" y="50" width="24" height="20" fill="#DDD9CF" stroke="#474040" strokeWidth="1.5" />
          {/* Keyway */}
          <rect x="52" y="44" width="18" height="6" fill="#C2BCAD" stroke="#474040" strokeWidth="1.2" />
          {/* Circlip groove */}
          <line x1="94" y1="50" x2="94" y2="70" stroke="#474040" strokeWidth="2" strokeDasharray="1 1" />
          {/* Center line */}
          <line x1="12" y1="60" x2="110" y2="60" stroke="#9E9696" strokeWidth="1" strokeDasharray="4 2 1 2" />
          {/* Bearing journal hatch */}
          <line x1="24" y1="53" x2="34" y2="67" stroke="#BBB5A7" strokeWidth="1" />
          <line x1="28" y1="53" x2="38" y2="67" stroke="#BBB5A7" strokeWidth="1" />
        </svg>
      );

    case 'stand':
      return (
        <svg viewBox="0 0 120 120" width="100%" height="100%" style={{ overflow: 'visible' }}>
          {/* Angled phone/tablet stand */}
          <polygon points="26,88 88,88 94,84 32,84" fill="#E2DDD2" stroke="#474040" strokeWidth="1.5" />
          <polygon points="32,84 56,32 64,32 40,84" fill="#D5CFC2" stroke="#474040" strokeWidth="1.6" />
          <polygon points="36,84 32,74 38,72 42,84" fill="#BDB5A6" stroke="#474040" strokeWidth="1.5" />
          {/* Back brace */}
          <polygon points="56,44 76,84 82,84 62,44" fill="#C7BFB0" stroke="#474040" strokeWidth="1.2" />
          {/* Cable hole */}
          <ellipse cx="48" cy="62" rx="4" ry="7" fill="#FAF9F5" stroke="#474040" strokeWidth="1.2" />
        </svg>
      );

    case 'heatsink':
      return (
        <svg viewBox="0 0 120 120" width="100%" height="100%" style={{ overflow: 'visible' }}>
          {/* Base plate */}
          <polygon points="20,78 70,62 100,74 50,90" fill="#D3CEBF" stroke="#474040" strokeWidth="1.5" />
          {/* Extruded fins */}
          {[0, 1, 2, 3, 4, 5].map(i => {
            const offset = i * 11;
            return (
              <polygon
                key={i}
                points={`${28 + offset * 0.8},${74 - offset * 0.2} ${28 + offset * 0.8},${34 - offset * 0.2} ${34 + offset * 0.8},${32 - offset * 0.2} ${34 + offset * 0.8},${72 - offset * 0.2}`}
                fill="#E8E5DD"
                stroke="#474040"
                strokeWidth="1.2"
              />
            );
          })}
        </svg>
      );

    case 'flange':
      return (
        <svg viewBox="0 0 120 120" width="100%" height="100%" style={{ overflow: 'visible' }}>
          {/* Raised face flange */}
          <ellipse cx="60" cy="60" rx="42" ry="26" fill="#DDD9CF" stroke="#474040" strokeWidth="1.6" />
          <ellipse cx="60" cy="56" rx="26" ry="16" fill="#E8E5DC" stroke="#474040" strokeWidth="1.4" />
          <ellipse cx="60" cy="56" rx="14" ry="8" fill="#FAF9F5" stroke="#474040" strokeWidth="1.6" />
          {/* Bolt holes */}
          {[0, 45, 90, 135, 180, 225, 270, 315].map((ang, i) => {
            const rad = (ang * Math.PI) / 180;
            const bx = 60 + 34 * Math.cos(rad);
            const by = 60 + 20 * Math.sin(rad);
            return <ellipse key={i} cx={bx} cy={by} rx="3" ry="2" fill="#FAF9F5" stroke="#474040" strokeWidth="1" />;
          })}
        </svg>
      );

    case 'duct':
      return (
        <svg viewBox="0 0 120 120" width="100%" height="100%" style={{ overflow: 'visible' }}>
          {/* Swept elbow / nozzle */}
          <path d="M 30,84 C 30,50 50,30 84,30 L 92,38 C 62,38 42,58 38,92 Z" fill="#DDD8CE" stroke="#474040" strokeWidth="1.6" />
          <ellipse cx="34" cy="88" rx="10" ry="5" fill="#C5BEB0" stroke="#474040" strokeWidth="1.4" />
          <ellipse cx="88" cy="34" rx="5" ry="10" fill="#C5BEB0" stroke="#474040" strokeWidth="1.4" />
          {/* Flow centerline */}
          <path d="M 34,88 C 34,54 54,34 88,34" fill="none" stroke="#9A9292" strokeWidth="1" strokeDasharray="3 2" />
        </svg>
      );

    default:
      return (
        <svg viewBox="0 0 120 120" width="100%" height="100%" style={{ overflow: 'visible' }}>
          {/* Isometric CAD cube with coordinate axes */}
          <polygon points="60,28 90,44 60,60 30,44" fill="#E8E5DC" stroke="#474040" strokeWidth="1.6" />
          <polygon points="30,44 60,60 60,94 30,78" fill="#D3CEBF" stroke="#474040" strokeWidth="1.6" />
          <polygon points="60,60 90,44 90,78 60,94" fill="#BBB4A3" stroke="#474040" strokeWidth="1.6" />
          {/* Axes callouts */}
          <line x1="60" y1="60" x2="60" y2="18" stroke="#D9534F" strokeWidth="1.4" strokeDasharray="2 1" />
          <line x1="60" y1="60" x2="98" y2="76" stroke="#489235" strokeWidth="1.4" strokeDasharray="2 1" />
          <line x1="60" y1="60" x2="22" y2="76" stroke="#337AB7" strokeWidth="1.4" strokeDasharray="2 1" />
        </svg>
      );
  }
}

export default function ModelThumbnail({ item }) {
  const archetype = detectArchetype(item);
  const meshInfo = item.mesh_info || {};
  const isWatertight = meshInfo.is_watertight;
  const faceCount = meshInfo.face_count;

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #ECECE4 0%, #F5F4EE 100%)',
        overflow: 'hidden',
        userSelect: 'none',
      }}
    >
      {/* Precision Blueprint Grid Backdrop */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `
            linear-gradient(to right, rgba(71, 64, 64, 0.06) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(71, 64, 64, 0.06) 1px, transparent 1px)
          `,
          backgroundSize: '16px 16px',
          opacity: 0.8,
        }}
      />

      {/* Crosshair marks in corners */}
      <div style={{ position: 'absolute', top: '8px', left: '8px', opacity: 0.35, fontSize: '10px', color: '#474040', fontFamily: 'monospace' }}>
        +
      </div>
      <div style={{ position: 'absolute', top: '8px', right: '8px', opacity: 0.35, fontSize: '10px', color: '#474040', fontFamily: 'monospace' }}>
        +
      </div>
      <div style={{ position: 'absolute', bottom: '8px', left: '8px', opacity: 0.35, fontSize: '10px', color: '#474040', fontFamily: 'monospace' }}>
        +
      </div>

      {/* Dynamic Vector CAD Geometry */}
      <div style={{ width: '104px', height: '104px', position: 'relative', zIndex: 1, filter: 'drop-shadow(0 4px 6px rgba(71,64,64,0.12))' }}>
        <ArchetypeGeometry type={archetype} />
      </div>

      {/* Technical Spec Badge (Bottom-Right) */}
      <div
        style={{
          position: 'absolute',
          bottom: '8px',
          right: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          background: 'rgba(255, 255, 255, 0.88)',
          backdropFilter: 'blur(4px)',
          border: '1px solid rgba(71, 64, 64, 0.15)',
          borderRadius: '4px',
          padding: '2px 6px',
          fontSize: '9px',
          fontWeight: 700,
          fontFamily: 'var(--font-mono, monospace)',
          color: '#474040',
          letterSpacing: '0.04em',
          zIndex: 2,
        }}
      >
        <span style={{ color: isWatertight ? '#489235' : '#888' }}>●</span>
        <span>{isWatertight ? 'SOLID' : 'MESH'}</span>
        {faceCount ? <span style={{ opacity: 0.6 }}>· {faceCount}f</span> : null}
      </div>
    </div>
  );
}
