const raw = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// On HTTPS pages, silently upgrade any http:// backend URL to https://
// to prevent mixed-content blocks when the env var is misconfigured.
const API_BASE =
  typeof window !== 'undefined' && window.location.protocol === 'https:'
    ? raw.replace(/^http:\/\//, 'https://')
    : raw;

export const apiFetch = (path: string, options: RequestInit = {}) => {
  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'ngrok-skip-browser-warning': 'true',
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });
};

export default API_BASE;
