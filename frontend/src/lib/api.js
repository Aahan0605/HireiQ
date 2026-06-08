// Global Fetch Interceptor to automatically attach JWT authorization tokens.
// This executes transparently on all window.fetch calls throughout the app.

const originalFetch = window.fetch;

window.fetch = async function (url, options = {}) {
  const token = localStorage.getItem('hireiq_token');
  
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
    const response = await originalFetch(url, options);
    
    // Auto-logout if unauthorized (401)
    if (response.status === 401 && !url.includes('/auth/login') && !url.includes('/auth/register')) {
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
