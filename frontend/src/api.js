// In dev, /api is proxied to the backend. In production, set VITE_API_URL.
const BASE = import.meta.env.VITE_API_URL || "";

async function get(path, params = {}) {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE}${path}${qs ? `?${qs}` : ""}`);
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

export const fetchMeta = () => get("/api/meta");
export const fetchSeries = (params) => get("/api/series", params);
export const fetchMetrics = (params) => get("/api/metrics", params);
export const fetchByHorizon = (params) => get("/api/metrics/by-horizon", params);