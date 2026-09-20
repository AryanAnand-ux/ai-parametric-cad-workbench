import React, { useState, useEffect } from 'react';

const TOUR_STEPS = [
  {
    id: 'prompt',
    title: 'Natural Language CAD Synthesis',
    badge: 'Step 1 of 5',
    icon: '⚡',
    description:
      'Describe any mechanical part using engineering terminology or plain language. Our 4-tier fallback synthesizes build123d Python scripts grounded by a vector index of 101 CAD templates.',
    tip: 'Try one of the presets like "CPU Heatsink" or "Mounting Bracket" on the left panel to explore immediately.',
  },
  {
    id: 'viewport',
    title: 'Real-Time 3D Solid Viewport',
    badge: 'Step 2 of 5',
    icon: '📐',
    description:
      'Inspect true boundary-representation (B-Rep) solid geometry. Use left-click to orbit, right-click to pan, and scroll to zoom. The ViewCube provides instantaneous isometric and orthographic camera views.',
    tip: 'Toggle "Shaded Edges" (EDGES) or "Bounding Dimensions" (DIMS) at the bottom status bar.',
  },
  {
    id: 'sliders',
    title: 'Sub-200ms Parametric Sliders',
    badge: 'Step 3 of 5',
    icon: '🎛️',
    description:
      'Every dimension, hole radius, wall thickness, and pitch angle is exposed as an interactive slider. Dragging sliders recomputes geometry directly in the OpenCASCADE kernel with no slow LLM re-calls.',
    tip: 'Watch the Telemetry HUD update the part envelope and volume live as you move sliders.',
  },
  {
    id: 'modify',
    title: 'Conversational Chat-to-Modify',
    badge: 'Step 4 of 5',
    icon: '💬',
    description:
      'Need an engineering revision? Chat naturally with your design. Ask to "add 4x M4 corner holes", "make walls 2mm thicker", or "fillet all vertical edges". Self-correction ensures valid geometry topology.',
    tip: 'Use the quick modification action buttons below the sliders to apply standard mechanical deltas.',
  },
  {
    id: 'export',
    title: 'Manufacturing & CNC Export',
    badge: 'Step 5 of 5',
    icon: '🚀',
    description:
      'Export production-grade STEP files for SolidWorks, Fusion 360, and CNC toolpath programming, or watertight STL meshes optimized for additive manufacturing. Inspect the raw Python CAD source code anytime.',
    tip: 'Click "Export" in the top navbar to download your files or "Inspect Code" to see the generated Python script.',
  },
];

export default function OnboardingTour({ isOpen, onClose }) {
  const [currentStep, setCurrentStep] = useState(0);

  const handleDismiss = () => {
    localStorage.setItem('cad_tour_completed', '1');
    onClose();
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!isOpen) return;
      if (e.key === 'Escape') handleDismiss();
      if (e.key === 'ArrowRight') handleNext();
      if (e.key === 'ArrowLeft') handlePrev();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, currentStep]);

  if (!isOpen) return null;

  const step = TOUR_STEPS[currentStep];

  const handleNext = () => {
    if (currentStep < TOUR_STEPS.length - 1) {
      setCurrentStep((s) => s + 1);
    } else {
      // Mark tour as completed so it doesn't auto-show next session
      localStorage.setItem('cad_tour_completed', '1');
      onClose();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep((s) => s - 1);
    }
  };

  return (
    <div className="modal-backdrop" onClick={handleDismiss}>
      <div
        className="modal-card"
        style={{ maxWidth: '520px' }}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        {/* Atelier Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <span style={{ fontSize: '18px' }}>{step.icon}</span>
            <div>
              <div className="modal-title">{step.title}</div>
              <div className="modal-subtitle">{step.badge} — CAD Studio Guide</div>
            </div>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={handleDismiss}
            aria-label="Skip tour"
          >
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '24px 28px', background: 'var(--bg-card)' }}>
          {/* Step Progress Bar */}
          <div style={{ display: 'flex', gap: '6px', marginBottom: '20px' }}>
            {TOUR_STEPS.map((s, idx) => (
              <div
                key={s.id}
                onClick={() => setCurrentStep(idx)}
                style={{
                  flex: 1,
                  height: '4px',
                  borderRadius: '2px',
                  background: idx === currentStep
                    ? '#474040'
                    : idx < currentStep
                    ? '#489235'
                    : '#E8E5DD',
                  cursor: 'pointer',
                  transition: 'background 0.2s ease',
                }}
              />
            ))}
          </div>

          {/* Description */}
          <p
            style={{
              margin: '0 0 16px',
              fontSize: '13px',
              lineHeight: 1.6,
              color: '#6B6363',
            }}
          >
            {step.description}
          </p>

          {/* Engineering Pro-Tip Box */}
          <div
            style={{
              background: '#F6F6F0',
              border: '1px solid rgba(71, 64, 64, 0.12)',
              borderRadius: '6px',
              padding: '12px 14px',
              marginBottom: '24px',
              fontSize: '12px',
              color: '#474040',
              display: 'flex',
              gap: '8px',
            }}
          >
            <span style={{ fontWeight: 700 }}>💡 Tip:</span>
            <span>{step.tip}</span>
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <button
              type="button"
              onClick={handlePrev}
              disabled={currentStep === 0}
              style={{
                padding: '8px 16px',
                background: 'transparent',
                border: '1px solid rgba(71, 64, 64, 0.2)',
                borderRadius: '6px',
                color: currentStep === 0 ? '#C0BBB8' : '#474040',
                cursor: currentStep === 0 ? 'not-allowed' : 'pointer',
                fontWeight: 600,
                fontSize: '12px',
              }}
            >
              ← Previous
            </button>

            <button
              type="button"
              onClick={handleNext}
              style={{
                padding: '9px 20px',
                background: '#474040',
                border: 'none',
                borderRadius: '6px',
                color: '#FFFDE2',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '12px',
                transition: 'background 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = '#363131')}
              onMouseLeave={(e) => (e.currentTarget.style.background = '#474040')}
            >
              {currentStep === TOUR_STEPS.length - 1 ? 'Start Modeling 🚀' : 'Next →'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
