/**
 * Authenticated fetch wrapper.
 * Automatically injects the JWT Bearer token from localStorage
 * into every request to the backend API.
 *
 * Usage:
 *   import { apiFetch } from '../lib/apiFetch';
 *   const res = await apiFetch('/api/v1/candidates');
 *   const data = await res.json();
 */
export function apiFetch(url, options = {}) {
  const token = localStorage.getItem('hireiq_token');
  const headers = {
    ...(options.headers || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Only set Content-Type for non-FormData bodies
  if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  return fetch(url, {
    ...options,
    headers,
  });
}
