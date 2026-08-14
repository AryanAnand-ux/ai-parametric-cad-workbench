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

  const pct = ((value - param.min) / (param.max - param.min)) * 100;

  return (
    <div className="param-item">
      <div className="param-header">
        <span className="param-label">{param.label}</span>
        <span className="param-value">{value.toFixed(param.step < 1 ? 1 : 0)} mm</span>
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
