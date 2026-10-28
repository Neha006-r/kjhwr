import { useEffect, useState } from "react";
import { fetchByHorizon, fetchMetrics, fetchSeries } from "./api";
import Controls from "./components/Controls";
import MetricCards from "./components/MetricCards";
import { ErrorChart, ForecastChart, HorizonChart, HourChart } from "./components/Charts";

// The API treats `end` as exclusive, while the UI date is inclusive.
function nextDay(dateStr) {
  const d = new Date(`${dateStr}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0, 10);
}

export default function App() {
  const [start, setStart] = useState("2026-01-01");
  const [end, setEnd] = useState("2026-01-07");
  const [horizon, setHorizon] = useState(24);

  const [series, setSeries] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [byHorizon, setByHorizon] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const invalidRange = start > end;

  useEffect(() => {
    if (invalidRange) return;
    let cancelled = false;
    const range = { start, end: nextDay(end) };

    setLoading(true);
    setError(null);
    Promise.all([
      fetchSeries({ ...range, horizon }),
      fetchMetrics({ ...range, horizon }),
      fetchByHorizon(range),
    ])
      .then(([s, m, h]) => {
        if (cancelled) return;
        setSeries(s);
        setMetrics(m);
        setByHorizon(h);
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));

    return () => { cancelled = true; };
  }, [start, end, horizon, invalidRange]);

  return (
    <div className="app">
      <header>
        <h1>UK Wind Forecast Monitor</h1>
        <p className="muted">
          Day-ahead purchasing: what the wind forecast said, and how accurate it was. Data: Elexon FUELHH and WINDFOR, January 2026.
        </p>
      </header>

      <Controls start={start} end={end} horizon={horizon}
        onStart={setStart} onEnd={setEnd} onHorizon={setHorizon} />

      {invalidRange && <div className="status error">The start date must be on or before the end date.</div>}
      {error && <div className="status error">Could not load data: {error}</div>}
      {loading && <div className="status loading">Loading...</div>}

      {!invalidRange && metrics && (
        <>
          <MetricCards summary={metrics.summary} />
          <p className="muted">
            Error = forecast minus actual (positive = the forecast was too high). Accuracy is measured on the
            hours present in both datasets: the forecast data is hourly and the actual data is half-hourly.
          </p>
          <ForecastChart data={series} />
          <div className="grid-2">
            <ErrorChart data={series} />
            <HourChart data={metrics.by_hour_of_day} />
          </div>
          <HorizonChart data={byHorizon} />
        </>
      )}
    </div>
  );
}