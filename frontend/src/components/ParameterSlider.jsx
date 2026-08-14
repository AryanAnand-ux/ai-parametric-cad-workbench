/**
 * ParameterSlider.jsx — Real-time parametric slider control
 *
 * Props:
 *   param   - { name, label, type, default, min, max, step }
 *   value   - current value
 *   onChange(name, value) - called on every slider change
 */

export default function ParameterSlider({ param, value, onChange }) {
  const handleChange = (e) => {
    onChange(param.name, parseFloat(e.target.value));
  };

  // Safe percentage calculation — prevents NaN / Infinity if min === max
  const range = param.max - param.min;
  const pct = range <= 0 ? 0 : Math.max(0, Math.min(100, ((value - param.min) / range) * 100));

  // Dynamic decimal places based on step precision
  const decimals = Number.isInteger(param.step)
    ? 0
    : (param.step.toString().split('.')[1]?.length || 1);

  const displayVal = typeof value === 'number' && !isNaN(value)
    ? value.toFixed(decimals)
    : param.default;

  return (
    <div className="param-item">
      <div className="param-header">
        <span className="param-label">{param.label}</span>
        <span className="param-value">{displayVal} mm</span>
      </div>

      <input
        id={`slider-${param.name}`}
        className="param-slider"
        type="range"
        min={param.min}
        max={param.max}
        step={param.step}
        value={value}
        onChange={handleChange}
        style={{
          background: `linear-gradient(to right, var(--accent) ${pct}%, var(--bg-input) ${pct}%)`
        }}
      />

      <div className="param-range-labels">
        <span className="param-range-label">{param.min}</span>
        <span className="param-range-label">{param.max}</span>
      </div>
    </div>
  );
}
