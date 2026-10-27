const fmt = (v) => (v == null ? "n/a" : Math.round(v).toLocaleString("en-GB"));

export default function MetricCards({ summary }) {
  if (!summary) return null;
  const bias = summary.bias;
  const biasText = bias == null ? "" : bias > 0 ? "over-forecasting" : "under-forecasting";
  const cards = [
    { label: "Mean absolute error (MAE)", value: `${fmt(summary.mae)} MW`,
      hint: summary.mae_pct_of_mean_actual != null ? `${summary.mae_pct_of_mean_actual.toFixed(1)}% of mean output` : "" },
    { label: "RMSE", value: `${fmt(summary.rmse)} MW`, hint: "Penalises large misses" },
    { label: "Bias (forecast - actual)", value: `${bias > 0 ? "+" : ""}${fmt(bias)} MW`, hint: biasText },
    { label: "P90 absolute error", value: `${fmt(summary.p90_abs_error)} MW`, hint: "9 in 10 hours are within this" },
    { label: "P99 absolute error", value: `${fmt(summary.p99_abs_error)} MW`, hint: "Near worst case" },
    { label: "Hours compared", value: summary.n.toLocaleString("en-GB"), hint: "Hours with both actual and forecast" },
  ];
  return (
    <div className="metrics">
      {cards.map((c) => (
        <div className="metric" key={c.label}>
          <div className="label">{c.label}</div>
          <div className="value">{c.value}</div>
          <div className="hint">{c.hint}</div>
        </div>
      ))}
    </div>
  );
}