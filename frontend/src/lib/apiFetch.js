/**
 * Authenticated fetch wrapper.
 * Automatically injects the JWT Bearer token from localStorage
 * into every request to the backend API.
 * Intercepts 401 Unauthorized responses to clear token/user and redirect to /signin.
 */
export async function apiFetch(url, options = {}) {
  const token = localStorage.getItem('hireiq_token');
  const headers = { ...(options.headers || {}) };

  if (token) headers['Authorization'] = `Bearer ${token}`;

  if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401) {
    localStorage.removeItem('hireiq_token');
    localStorage.removeItem('hireiq_user');
    window.location.href = '/signin';
    return res;
  }

  return res;
}
