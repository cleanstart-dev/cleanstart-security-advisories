const DEFAULT_API_BASE =
  (typeof window !== "undefined" && window.API_BASE_URL) ||
  process.env.REACT_APP_API_BASE ||
  "http://localhost:5000";

export const API_BASE = DEFAULT_API_BASE.replace(/\/+$/, "");

export function apiUrl(path = "") {
  if (!path.startsWith("/")) {
    path = `/${path}`;
  }
  return `${API_BASE}${path}`;
}

export function apiFetch(path, options) {
  return fetch(apiUrl(path), options);
}
