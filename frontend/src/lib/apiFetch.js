import { toast } from 'react-hot-toast';

/**
 * Authenticated fetch wrapper.
 * Automatically injects the JWT Bearer token from localStorage
 * into every request to the backend API.
 * Intercepts 401 Unauthorized responses to clear token/user and redirect to /signin.
 * Triggers error toast notifications for non-2xx failures.
 */
export async function apiFetch(url, options = {}) {
  const token = localStorage.getItem('hireiq_token');
  const headers = { ...(options.headers || {}) };

  if (token) headers['Authorization'] = `Bearer ${token}`;

  if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  try {
    const res = await fetch(url, { ...options, headers });

    if (res.status === 401) {
      localStorage.removeItem('hireiq_token');
      localStorage.removeItem('hireiq_user');
      // Only redirect if not already on sign-in pages to prevent redirect loops
      if (!window.location.pathname.startsWith('/signin') && !window.location.pathname.startsWith('/verify-email') && !window.location.pathname.startsWith('/forgot-password') && !window.location.pathname.startsWith('/reset-password')) {
        window.location.href = '/signin';
      }
      return res;
    }

    if (res.status >= 400) {
      try {
        const cloned = res.clone();
        const data = await cloned.json();
        const msg = data.detail || data.message || `Request failed with status ${res.status}`;
        toast.error(msg);
      } catch (e) {
        toast.error(`Request failed with status ${res.status}`);
      }
    }

    return res;
  } catch (err) {
    toast.error('Network connection error. Please try again.');
    throw err;
  }
}
