export default function Controls({ start, end, horizon, onStart, onEnd, onHorizon }) {
  return (
    <section className="card">
      <div className="controls">
        <label className="field">
          <span>From</span>
          <input type="date" value={start} min="2026-01-01" max="2026-01-31"
            onChange={(e) => onStart(e.target.value)} />
        </label>
        <label className="field">
          <span>To (inclusive)</span>
          <input type="date" value={end} min="2026-01-01" max="2026-01-31"
            onChange={(e) => onEnd(e.target.value)} />
        </label>
        <label className="field">
          <span>Forecast horizon: <strong>{horizon} h</strong> before delivery</span>
          <input type="range" min="0" max="48" step="1" value={horizon}
            onChange={(e) => onHorizon(Number(e.target.value))} />
        </label>
      </div>
      <p className="muted" style={{ marginTop: 12 }}>
        For each hour, we use the latest forecast published at least {horizon} hours earlier,
        which is what a buyer could actually see when committing to the day-ahead market. Times are UTC (= UK time in January).
      </p>
    </section>
  );
}