/**
 * ParameterSlider.jsx — Real-time parametric slider control
 *
 * Props:
 *   param   - { name, label, type, default, min, max, step }
 *   value   - current value
 *   onChange(name, value) - called on every slider change
 */

export default function ParameterSlider({ param, value, onChange }) {
  // Defensive fallback for steps that the backend may omit on some payloads
  const stepVal = param.step ?? 1.0;
  // Dynamic decimal places based on step precision — computed FIRST so it's
  // available inside handleStepChange (which would cause a ReferenceError otherwise)
  const decimals = Number.isInteger(stepVal)
    ? 0
    : (stepVal.toString().split('.')[1]?.length || 1);

  // Safe percentage calculation — prevents NaN / Infinity if min === max
  const range = param.max - param.min;
  const numValue = typeof value === 'number' && !isNaN(value) ? value : param.default;
  const pct = range <= 0 ? 0 : Math.max(0, Math.min(100, ((numValue - param.min) / range) * 100));

  const handleChange = (e) => {
    const val = parseFloat(e.target.value);
    if (!isNaN(val)) {
      onChange(param.name, val);
    }
  };

  const handleReset = () => {
    onChange(param.name, param.default);
  };

  const handleStepChange = (direction) => {
    const current = typeof value === 'number' && !isNaN(value) ? value : param.default;
    const next = Math.max(param.min, Math.min(param.max, current + direction * stepVal));
    onChange(param.name, parseFloat(next.toFixed(decimals)));
  };

  const displayVal = numValue.toFixed(decimals);

  // Unit formatting
  let unit = '';
  if (param.unit) {
    unit = (param.unit === 'deg' || param.unit === '°') ? '°' : (param.unit === 'mm' ? 'mm' : param.unit);
  } else {
    const lowerName = param.name.toLowerCase();
    unit = lowerName.includes('angle') || lowerName.includes('deg')
      ? '°'
      : (lowerName.includes('count') || lowerName.includes('num') || param.type === 'integer' ? '' : 'mm');
  }

  const isModified = Math.abs(numValue - param.default) > 0.0001;

  return (
    <div className={`param-item ${isModified ? 'param-item--modified' : ''}`}>
      <div className="param-header">
        <div className="param-label-group">
          <span className="param-label">{param.label || param.name}</span>
          {param.name && <span className="param-var-tag">{param.name}</span>}
        </div>
        <div className="param-controls-group">
          <div className="param-value-box">
            <input
              aria-label={`${param.label || param.name} value`}
              type="number"
              className="param-number-input"
              value={displayVal}
              min={param.min}
              max={param.max}
              step={param.step}
              onChange={handleChange}
            />
            {unit && <span className="param-unit-badge">{unit}</span>}
          </div>
          {isModified && (
            <button
              onClick={handleReset}
              className="param-reset-btn"
              title={`Reset to default (${param.default}${unit})`}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
            >
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 10h10a5 5 0 0 1 5 5v2"/>
                <polyline points="7 6 3 10 7 14"/>
              </svg>
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>

      <div className="param-slider-wrapper">
        <button
          type="button"
          className="param-stepper-btn"
          onClick={() => handleStepChange(-1)}
          title={`Decrease by ${stepVal}`}
        >
          -
        </button>

        <div className="param-slider-container">
          <input
            aria-label={param.label || param.name}
            id={`slider-${param.name}`}
            className="param-slider"
            type="range"
            min={param.min}
            max={param.max}
            step={param.step}
            value={numValue}
            onChange={handleChange}
            style={{
              background: `linear-gradient(to right, #474040 ${pct}%, #E8E5DD ${pct}%)`
            }}
          />
        </div>

        <button
          type="button"
          className="param-stepper-btn"
          onClick={() => handleStepChange(1)}
          title={`Increase by ${stepVal}`}
        >
          +
        </button>
      </div>

      <div className="param-range-labels">
        <span className="param-range-label min">
          Min: <strong>{param.min}</strong>{unit}
        </span>
        <span className="param-range-label def">
          Default: <strong>{param.default}</strong>{unit}
        </span>
        <span className="param-range-label max">
          Max: <strong>{param.max}</strong>{unit}
        </span>
      </div>
    </div>
  );
}
