import React, { useState } from 'react';

/**
 * TelemetryHUD — CAD Model Telemetry, Watertight Manifold & ICLR 2025 Design Intent Metrics
 */
export default function TelemetryHUD({ meshInfo, recompTime, verificationReport }) {
  const [showIntentDetails, setShowIntentDetails] = useState(false);

  if (!meshInfo && !verificationReport) return null;

  const { dimensions_mm, volume_mm3, is_watertight, body_count, face_count } = meshInfo || {};

  const formatFaceCount = (count) => {
    if (count >= 1000) return `${(count / 1000).toFixed(1)}k`;
    return `${count}`;
  };

  const intentScore = verificationReport?.intent_score ?? null;
  const isVerified = verificationReport?.is_verified ?? false;

  return (
    <div style={{ position: 'relative' }}>
      <div className="sidebar-metrics-bar">
        {dimensions_mm && (
          <span className="sidebar-metric-chip" title="Bounding Box Envelope (X × Y × Z)">
            {dimensions_mm.x} × {dimensions_mm.y} × {dimensions_mm.z} mm
          </span>
        )}

        {volume_mm3 !== undefined && volume_mm3 !== null && (
          <span className="sidebar-metric-chip" title="Solid Volume">
            ◈ {(volume_mm3 / 1000).toFixed(1)} cm³
          </span>
        )}

        {is_watertight !== undefined && (
          <span
            className="sidebar-metric-chip"
            style={{ color: is_watertight ? '#10B981' : '#EF4444' }}
            title={is_watertight ? "Watertight 2-manifold B-Rep" : "Non-manifold boundary edges detected"}
          >
            ● {is_watertight ? 'Watertight' : 'Non-Manifold'}
          </span>
        )}

        {/* ICLR 2025 CADCodeVerify Design Intent Score Chip */}
        {verificationReport && intentScore !== null && (
          <button
            type="button"
            className="sidebar-metric-chip"
            style={{
              cursor: 'pointer',
              background: isVerified ? 'rgba(16, 185, 129, 0.12)' : 'rgba(245, 158, 11, 0.12)',
              color: isVerified ? '#10B981' : '#F59E0B',
              borderColor: isVerified ? 'rgba(16, 185, 129, 0.35)' : 'rgba(245, 158, 11, 0.35)',
              fontWeight: 600,
            }}
            onClick={() => setShowIntentDetails((prev) => !prev)}
            title="Click to view ICLR 2025 CADCodeVerify Intent Verification Report"
          >
            🎯 {Math.round(intentScore * 100)}% Intent ({verificationReport.passed_checks}/{verificationReport.total_checks})
          </button>
        )}

        {body_count !== undefined && body_count > 1 && (
          <span className="sidebar-metric-chip" title="Disjoint Solid Bodies">
            Bodies: {body_count}
          </span>
        )}

        {typeof face_count === 'number' && face_count > 0 && (
          <span className="sidebar-metric-chip" title="B-Rep Face Count">
            ⬡ {formatFaceCount(face_count)} faces
          </span>
        )}

        {recompTime && (
          <span className="sidebar-metric-chip" title="Kernel Execution Time">
            ⚡ {recompTime}ms
          </span>
        )}
      </div>

      {/* CADCodeVerify Detailed Verification Dropdown */}
      {showIntentDetails && verificationReport && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            zIndex: 40,
            marginTop: '6px',
            backgroundColor: '#0F172A',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            borderRadius: '8px',
            padding: '12px',
            boxShadow: '0 12px 24px -4px rgba(0, 0, 0, 0.5)',
            fontSize: '12px',
            color: '#E2E8F0',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '6px' }}>
            <span style={{ fontWeight: 600, color: '#38BDF8' }}>CADCodeVerify (ICLR 2025)</span>
            <button
              type="button"
              onClick={() => setShowIntentDetails(false)}
              style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer', fontSize: '14px' }}
            >
              ✕
            </button>
          </div>
          {verificationReport.part_summary && (
            <div style={{ color: '#94A3B8', marginBottom: '10px', lineHeight: '1.4' }}>
              {verificationReport.part_summary}
            </div>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {verificationReport.checks?.map((check, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '8px',
                  padding: '6px 8px',
                  borderRadius: '4px',
                  backgroundColor: check.passed ? 'rgba(16, 185, 129, 0.06)' : 'rgba(239, 68, 68, 0.08)',
                  borderLeft: `3px solid ${check.passed ? '#10B981' : '#EF4444'}`,
                }}
              >
                <span style={{ color: check.passed ? '#10B981' : '#EF4444', fontWeight: 'bold' }}>
                  {check.passed ? '✓' : '✗'}
                </span>
                <div>
                  <div style={{ fontWeight: 500, color: '#F8FAFC' }}>{check.criterion}</div>
                  <div style={{ color: '#94A3B8', fontSize: '11px', marginTop: '2px' }}>{check.explanation}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
