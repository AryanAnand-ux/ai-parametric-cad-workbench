import React from 'react';

const STAGES = [
  { id: 'rag_retrieval', label: 'Semantic Blueprint Retrieval', desc: 'ChromaDB vector match across 101 CAD templates' },
  { id: 'llm_generation', label: 'Parametric Code Synthesis', desc: 'build123d Python script generation via AI pipeline' },
  { id: 'ast_validation', label: 'AST Security & Sandbox Audit', desc: 'Syntax verification and security import validation' },
  { id: 'cad_execution', label: 'OpenCASCADE Kernel Compilation', desc: 'B-Rep solid modeling & tessellated mesh extraction' },
  { id: 'mesh_validation', label: 'Topology & Water-tightness Check', desc: 'Verifying 2-manifold solid and positive volume' },
];

export default function GenerationProgress({ currentPhase, progress = 0, message, attempts = 0 }) {
  const activeIndex = STAGES.findIndex((s) => s.id === currentPhase);
  const effectiveIndex = activeIndex === -1 ? (progress > 85 ? 4 : progress > 50 ? 3 : progress > 25 ? 1 : 0) : activeIndex;

  return (
    <div
      style={{
        width: '100%',
        maxWidth: '520px',
        background: '#FFFFFF',
        border: '1px solid rgba(71, 64, 64, 0.18)',
        borderRadius: '12px',
        boxShadow: '0 20px 50px rgba(71, 64, 64, 0.25)',
        overflow: 'hidden',
        color: '#474040',
        fontFamily: 'var(--font-sans)',
      }}
    >
      {/* Atelier Header */}
      <div
        style={{
          background: '#474040',
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid rgba(255, 253, 226, 0.15)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: '#489235',
              boxShadow: '0 0 8px #489235',
              animation: 'pulse 1.8s infinite',
            }}
          />
          <span
            style={{
              fontFamily: 'var(--font-serif)',
              fontSize: '17px',
              fontWeight: 500,
              fontStyle: 'italic',
              color: '#FFFDE2',
            }}
          >
            Synthesizing Solid B-Rep Geometry
          </span>
        </div>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            color: 'rgba(255, 253, 226, 0.8)',
            background: 'rgba(255, 253, 226, 0.1)',
            padding: '2px 8px',
            borderRadius: '12px',
          }}
        >
          {progress > 0 ? `${Math.round(progress)}%` : 'Active'}
        </span>
      </div>

      {/* Body */}
      <div style={{ padding: '20px 24px', background: '#F6F6F0' }}>
        {/* Progress Bar */}
        <div
          style={{
            width: '100%',
            height: '5px',
            background: '#E8E5DD',
            borderRadius: '3px',
            overflow: 'hidden',
            marginBottom: '18px',
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${Math.max(8, progress)}%`,
              background: '#474040',
              borderRadius: '3px',
              transition: 'width 0.3s ease-out',
            }}
          />
        </div>

        {/* Pipeline Stages */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {STAGES.map((stage, idx) => {
            const isDone = idx < effectiveIndex;
            const isCurrent = idx === effectiveIndex;

            return (
              <div
                key={stage.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  background: isCurrent
                    ? '#FFFFFF'
                    : isDone
                    ? 'rgba(72, 146, 53, 0.05)'
                    : 'transparent',
                  border: isCurrent
                    ? '1px solid rgba(71, 64, 64, 0.2)'
                    : '1px solid transparent',
                  boxShadow: isCurrent ? '0 2px 6px rgba(71, 64, 64, 0.06)' : 'none',
                  transition: 'all 0.15s ease',
                }}
              >
                {/* Status Dot */}
                <div
                  style={{
                    width: '20px',
                    height: '20px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '11px',
                    fontWeight: 700,
                    flexShrink: 0,
                    background: isDone ? '#489235' : isCurrent ? '#474040' : '#E8E5DD',
                    color: isDone || isCurrent ? '#FFFDE2' : '#99908F',
                  }}
                >
                  {isDone ? '✓' : idx + 1}
                </div>

                {/* Stage Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: '12px',
                      fontWeight: isCurrent ? 600 : 500,
                      color: isCurrent ? '#474040' : isDone ? '#6B6363' : '#99908F',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }}
                  >
                    {stage.label}
                    {isCurrent && attempts > 0 && (
                      <span
                        style={{
                          fontSize: '10px',
                          background: '#FEF3C7',
                          color: '#B45309',
                          padding: '1px 5px',
                          borderRadius: '4px',
                          fontWeight: 600,
                        }}
                      >
                        Retry #{attempts}
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: '10px', color: '#99908F', marginTop: '1px' }}>
                    {stage.desc}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Live Message */}
        {message && (
          <div
            style={{
              marginTop: '16px',
              padding: '8px 12px',
              background: '#FFFFFF',
              border: '1px solid rgba(71, 64, 64, 0.12)',
              borderRadius: '6px',
              fontSize: '11px',
              color: '#6B6363',
              fontFamily: 'var(--font-mono)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <span style={{ color: '#474040', fontWeight: 700 }}>›</span>
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{message}</span>
          </div>
        )}
      </div>
    </div>
  );
}
