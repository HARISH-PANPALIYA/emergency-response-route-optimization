const API_BASE_URL = import.meta.env.VITE_API_URL
  || import.meta.env.VITE_API_BASE_URL
  || (import.meta.env.DEV ? window.location.origin : "");

export function getToken() { return window.localStorage.getItem("emergency_access_token"); }
export function setToken(token) { window.localStorage.setItem("emergency_access_token", token); }
export function clearToken() { window.localStorage.removeItem("emergency_access_token"); }

async function request(path, options = {}) {
  if (!API_BASE_URL) {
    throw new Error("The response service URL is not configured.");
  }
  const headers = new Headers(options.headers || {});
  const token = getToken();
  if (token) headers.set("Authorization", "Bearer " + token);
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.detail || `Request failed: ${response.status}`);
  return body;
}
export function apiGet(path) { return request(path); }
export function apiPost(path, body) { return request(path, { method: "POST", body: JSON.stringify(body) }); }
export function apiPatch(path, body) { return request(path, { method: "PATCH", body: JSON.stringify(body) }); }
export async function login(email, password) { const result = await apiPost("/auth/login", { email, password }); setToken(result.access_token); return result; }
export async function register(email, password) { const result = await apiPost("/auth/register", { email, password }); setToken(result.access_token); return result; }
