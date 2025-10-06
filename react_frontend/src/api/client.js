const API_BASE = process.env.REACT_APP_API_BASE || '';

/**
 * Lightweight API client for the Slack Query Tracker frontend.
 * Uses fetch and returns JSON or throws errors with standardized messages.
 */

// Internal: handle fetch responses
async function handleResponse(res) {
  const contentType = res.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');

  if (!res.ok) {
    let message = `Request failed with status ${res.status}`;
    if (isJson) {
      const data = await res.json().catch(() => null);
      if (data && (data.error || data.message)) {
        message = data.error || data.message;
      }
    } else {
      const text = await res.text().catch(() => '');
      if (text) message = text;
    }
    const err = new Error(message);
    err.status = res.status;
    throw err;
  }

  if (isJson) return res.json();
  return res;
}

// PUBLIC_INTERFACE
export async function getChannelConfig() {
  /** Fetch the saved Slack channel configuration. */
  const res = await fetch(`${API_BASE}/api/config/channel`, { method: 'GET' });
  return handleResponse(res);
}

// PUBLIC_INTERFACE
export async function saveChannelConfig(payload) {
  /** Save or update the Slack channel configuration. */
  const res = await fetch(`${API_BASE}/api/config/channel`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

// PUBLIC_INTERFACE
export async function listQueries({ page = 1, pageSize = 10, status = '', search = '' } = {}) {
  /** Get list of queries with optional filtering and pagination. */
  const params = new URLSearchParams();
  params.set('page', page);
  params.set('pageSize', pageSize);
  if (status) params.set('status', status);
  if (search) params.set('search', search);

  const res = await fetch(`${API_BASE}/api/queries?${params.toString()}`, { method: 'GET' });
  return handleResponse(res);
}

// PUBLIC_INTERFACE
export async function createQuery(payload) {
  /** Create a new query item. */
  const res = await fetch(`${API_BASE}/api/queries`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

// PUBLIC_INTERFACE
export async function updateQuery(id, payload) {
  /** Update query by ID. Partial updates supported. */
  const res = await fetch(`${API_BASE}/api/queries/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

// PUBLIC_INTERFACE
export async function deleteQuery(id) {
  /** Delete query by ID. */
  const res = await fetch(`${API_BASE}/api/queries/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
  return handleResponse(res);
}

// PUBLIC_INTERFACE
export async function fetchFromSlack() {
  /** Trigger Slack fetch on the backend. Returns job or result info. */
  const res = await fetch(`${API_BASE}/api/slack/fetch`, { method: 'POST' });
  return handleResponse(res);
}

// PUBLIC_INTERFACE
export async function exportToExcel() {
  /**
   * Request backend to generate an Excel export and return a Blob.
   * Caller is responsible for triggering download in the browser.
   */
  const res = await fetch(`${API_BASE}/api/export`, { method: 'POST' });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    const err = new Error(text || `Export failed with status ${res.status}`);
    err.status = res.status;
    throw err;
  }
  const blob = await res.blob();
  return blob;
}
