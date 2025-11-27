// Simple wrapper for API requests
async function apiRequest(path, options = {}) {
  const url = API_BASE + path;
  const headers = options.headers || {};
  if (sessionToken) {
    headers['X-Session-Token'] = sessionToken;
  }
  return fetch(url, { ...options, headers });
}
