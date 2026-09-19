import React from 'react';

/**
 * TelemetryHUD — CAD Model Telemetry, Watertight Manifold & Boundary Envelope Metrics
 */
export default function TelemetryHUD({ meshInfo, recompTime, modelUsed, designMode }) {
  if (!meshInfo) return null;

  const { dimensions_mm, volume_mm3, is_watertight, body_count } = meshInfo;

  return (
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

      {body_count !== undefined && body_count > 1 && (
        <span className="sidebar-metric-chip" title="Disjoint Solid Bodies">
          Bodies: {body_count}
        </span>
      )}

      {recompTime && (
        <span className="sidebar-metric-chip" title="Kernel Execution Time">
          ⚡ {recompTime}ms
        </span>
      )}
    </div>
  );
}
