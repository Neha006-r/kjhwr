import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from "recharts";

const fmtTime = (t) =>
  new Date(t).toLocaleString("en-GB", {
    timeZone: "UTC", day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
  });
const fmtMW = (v) => (v == null ? "" : Math.round(v).toLocaleString("en-GB"));
const tipMW = (v, name) => [`${fmtMW(v)} MW`, name];

function Card({ title, subtitle, empty, children }) {
  return (
    <section className="card">
      <h3>{title}</h3>
      {subtitle && <p className="muted">{subtitle}</p>}
      <div className="chart">{empty ? <p className="muted">No data for this selection.</p> : children}</div>
    </section>
  );
}

export function ForecastChart({ data }) {
  return (
    <Card title="Actual vs forecast wind generation"
      subtitle="Forecast shown is the latest one available at the chosen horizon" empty={!data.length}>
      <ResponsiveContainer>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="startTime" tickFormatter={fmtTime} minTickGap={50} />
          <YAxis tickFormatter={fmtMW} label={{ value: "MW", angle: -90, position: "insideLeft" }} />
          <Tooltip labelFormatter={fmtTime} formatter={tipMW} />
          <Legend />
          <Line type="monotone" dataKey="actual" name="Actual" stroke="#0b6cff" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="forecast" name="Forecast" stroke="#f97316" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}

export function ErrorChart({ data }) {
  return (
    <Card title="Forecast error over time"
      subtitle="Forecast minus actual. Above zero = over-forecast" empty={!data.length}>
      <ResponsiveContainer>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="startTime" tickFormatter={fmtTime} minTickGap={50} />
          <YAxis tickFormatter={fmtMW} />
          <Tooltip labelFormatter={fmtTime} formatter={tipMW} />
          <ReferenceLine y={0} stroke="#64748b" />
          <Line type="monotone" dataKey="error" name="Error" stroke="#dc2626" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}

export function HourChart({ data }) {
  return (
    <Card title="Error by hour of day (UTC)"
      subtitle="MAE and bias per hour" empty={!data.length}>
      <ResponsiveContainer>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="hour" />
          <YAxis tickFormatter={fmtMW} />
          <Tooltip formatter={tipMW} labelFormatter={(h) => `${h}:00`} />
          <Legend />
          <Bar dataKey="mae" name="MAE" fill="#0b6cff" />
          <Bar dataKey="bias" name="Bias" fill="#f97316" />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}

export function HorizonChart({ data }) {
  return (
    <Card title="Accuracy vs forecast horizon"
      subtitle="How error changes as the forecast gets older" empty={!data.length}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 28 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="horizon_hours"
            label={{ value: "hours before delivery", position: "insideBottom", offset: -18 }} />
          <YAxis tickFormatter={fmtMW} />
          <Tooltip formatter={tipMW} labelFormatter={(h) => `${h} h ahead`} />
          <Legend verticalAlign="top" />
          <Line type="monotone" dataKey="mae" name="MAE" stroke="#0b6cff" strokeWidth={2} />
          <Line type="monotone" dataKey="p90_abs_error" name="P90 error" stroke="#dc2626" strokeWidth={2} />
          <Line type="monotone" dataKey="bias" name="Bias" stroke="#f97316" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}