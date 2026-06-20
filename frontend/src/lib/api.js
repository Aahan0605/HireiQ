// Global Fetch Interceptor to automatically attach JWT authorization tokens.
// This executes transparently on all window.fetch calls throughout the app.

const originalFetch = window.fetch;

window.fetch = async function (url, options = {}) {
  const token = localStorage.getItem('hireiq_token');
  
  // Prepend VITE_API_URL dynamically if configured
  const apiBase = import.meta.env.VITE_API_URL || '';
  let finalUrl = url;
  if (apiBase && typeof url === 'string' && url.startsWith('/api/')) {
    const cleanBase = apiBase.replace(/\/$/, '');
    if (cleanBase.endsWith('/api/v1')) {
      finalUrl = `${cleanBase.replace(/\/api\/v1$/, '')}${url}`;
    } else if (cleanBase.endsWith('/api')) {
      finalUrl = `${cleanBase.replace(/\/api$/, '')}${url}`;
    } else {
      finalUrl = `${cleanBase}${url}`;
    }
  }

  // Create headers object if not exists
  options.headers = options.headers || {};

  // If we have a token, inject the Bearer header
  if (token) {
    if (options.headers instanceof Headers) {
      if (!options.headers.has('Authorization')) {
        options.headers.set('Authorization', `Bearer ${token}`);
      }
    } else if (Array.isArray(options.headers)) {
      const hasAuth = options.headers.some(([key]) => key.toLowerCase() === 'authorization');
      if (!hasAuth) {
        options.headers.push(['Authorization', `Bearer ${token}`]);
      }
    } else {
      if (!options.headers['Authorization'] && !options.headers['authorization']) {
        options.headers['Authorization'] = `Bearer ${token}`;
      }
    }
  }

  try {
    const response = await originalFetch(finalUrl, options);
    
    // Auto-logout if unauthorized (401)
    if (response.status === 401 && !finalUrl.includes('/auth/login') && !finalUrl.includes('/auth/register')) {
      console.warn("Unauthorized access - clearing token and redirecting to login.");
      localStorage.removeItem('hireiq_token');
      localStorage.removeItem('hireiq_user');
      // Redirect to signin
      if (window.location.pathname !== '/signin') {
        window.location.href = '/signin';
      }
    }
    
    return response;
  } catch (error) {
    return Promise.reject(error);
  }
};
