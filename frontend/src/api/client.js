export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  constructor(message, code, status) {
    super(message);
    this.code = code;
    this.status = status;
    this.name = 'ApiError';
  }
}

async function handleResponse(response) {
  if (response.ok) {
    // 204 No Content has no body
    if (response.status === 204) return null;
    return response.json();
  }

  let errorData;
  try {
    errorData = await response.json();
  } catch (err) {
    throw new ApiError('Failed to parse error response', 'PARSE_ERROR', response.status);
  }

  // The backend uses {"error": {"code": "...", "message": "..."}}
  const code = errorData?.error?.code || 'UNKNOWN_ERROR';
  const message = errorData?.error?.message || 'An unknown error occurred.';
  throw new ApiError(message, code, response.status);
}

export const client = {
  async get(endpoint, options = {}) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    return handleResponse(response);
  },

  async post(endpoint, data, options = {}) {
    // Detect if data is FormData
    const isFormData = data instanceof FormData;
    const headers = { ...options.headers };
    
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      method: 'POST',
      headers,
      body: isFormData ? data : JSON.stringify(data),
    });
    return handleResponse(response);
  },

  async delete(endpoint, options = {}) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    return handleResponse(response);
  },
};
