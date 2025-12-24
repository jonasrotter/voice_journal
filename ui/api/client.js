/**
 * API Client - Handles all HTTP communication with backend
 * @module api/client
 */

// In development, point to backend server; in production, use relative path
const DEV_PORTS = ['3000', '5173', '5174'];
const API_BASE = DEV_PORTS.includes(window.location.port)
    ? 'http://localhost:8000/api/v1' 
    : '/api/v1';

/**
 * Get stored auth token
 * @returns {string|null}
 */
function getToken() {
    return localStorage.getItem('access_token');
}

/**
 * Store auth token
 * @param {string} token
 */
export function setToken(token) {
    localStorage.setItem('access_token', token);
}

/**
 * Clear auth token
 */
export function clearToken() {
    localStorage.removeItem('access_token');
}

/**
 * Check if user is authenticated
 * @returns {boolean}
 */
export function isAuthenticated() {
    return !!getToken();
}

/**
 * Build request headers
 * @param {boolean} includeAuth
 * @returns {Headers}
 */
function buildHeaders(includeAuth = true) {
    const headers = new Headers();
    headers.append('Content-Type', 'application/json');
    
    if (includeAuth) {
        const token = getToken();
        if (token) {
            headers.append('Authorization', `Bearer ${token}`);
        }
    }
    
    return headers;
}

/**
 * Generic API request handler
 * @param {string} endpoint
 * @param {Object} options
 * @returns {Promise<any>}
 */
async function request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
        ...options,
        headers: options.headers || buildHeaders(options.auth !== false)
    };
    
    try {
        const response = await fetch(url, config);
        
        if (response.status === 401) {
            clearToken();
            window.dispatchEvent(new CustomEvent('auth:logout'));
            throw new Error('Session expired');
        }
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Request failed: ${response.status}`);
        }
        
        // Handle empty responses
        const text = await response.text();
        return text ? JSON.parse(text) : null;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ============ Auth API ============

/**
 * Register new user
 * @param {string} email
 * @param {string} password
 * @returns {Promise<import('./types').User>}
 */
export async function register(email, password) {
    return request('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
        auth: false
    });
}

/**
 * Login user
 * @param {string} email
 * @param {string} password
 * @returns {Promise<import('./types').Token>}
 */
export async function login(email, password) {
    const data = await request('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
        auth: false
    });
    
    if (data.access_token) {
        setToken(data.access_token);
    }
    
    return data;
}

/**
 * Logout user
 */
export function logout() {
    clearToken();
    window.dispatchEvent(new CustomEvent('auth:logout'));
}

// ============ Users API ============

/**
 * Get current user
 * @returns {Promise<import('./types').User>}
 */
export async function getCurrentUser() {
    return request('/users/me');
}

/**
 * Update current user
 * @param {Object} updates
 * @returns {Promise<import('./types').User>}
 */
export async function updateCurrentUser(updates) {
    return request('/users/me', {
        method: 'PATCH',
        body: JSON.stringify(updates)
    });
}

// ============ Entries API ============

/**
 * Upload audio entry
 * @param {Blob} audioBlob
 * @returns {Promise<import('./types').EntryCreateResponse>}
 */
export async function uploadEntry(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    
    const token = getToken();
    const headers = new Headers();
    if (token) {
        headers.append('Authorization', `Bearer ${token}`);
    }
    
    const response = await fetch(`${API_BASE}/entries`, {
        method: 'POST',
        headers,
        body: formData
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Upload failed');
    }
    
    return response.json();
}

/**
 * Get all entries
 * @param {Object} params
 * @param {number} [params.page=1]
 * @param {number} [params.page_size=50]
 * @returns {Promise<import('./types').EntryListResponse>}
 */
export async function getEntries(params = {}) {
    const { page = 1, page_size = 50 } = params;
    return request(`/entries?page=${page}&page_size=${page_size}`);
}

/**
 * Get single entry
 * @param {string} entryId
 * @returns {Promise<import('./types').JournalEntry>}
 */
export async function getEntry(entryId) {
    return request(`/entries/${entryId}`);
}

/**
 * Delete entry
 * @param {string} entryId
 * @returns {Promise<void>}
 */
export async function deleteEntry(entryId) {
    return request(`/entries/${entryId}`, {
        method: 'DELETE'
    });
}

/**
 * Reprocess entry
 * @param {string} entryId
 * @returns {Promise<import('./types').JournalEntry>}
 */
export async function reprocessEntry(entryId) {
    return request(`/entries/${entryId}/reprocess`, {
        method: 'POST'
    });
}

// ============ Audio URL Helper ============

/**
 * Get full audio URL - returns direct URL for local files or legacy URLs
 * @param {string} audioUrl - Audio URL from entry
 * @returns {string} Full URL
 * @deprecated Use fetchAudioBlob with entry ID for Azure Blob Storage
 */
export function getAudioUrl(audioUrl) {
    if (audioUrl.startsWith('http')) {
        return audioUrl;
    }
    // Audio files are served from /uploads/audio/
    return `/uploads/audio/${audioUrl.split('/').pop()}`;
}

/**
 * Get audio stream URL via backend proxy
 * This endpoint streams audio from Azure Blob Storage through the backend,
 * handling authentication with DefaultAzureCredential (Azure CLI locally, Managed Identity in Azure).
 * @param {string} entryId - Entry UUID
 * @returns {string} Full URL to audio stream endpoint
 */
export function getAudioStreamUrl(entryId) {
    return `${API_BASE}/entries/${entryId}/audio`;
}

/**
 * Fetch audio as Blob with authentication
 * HTML audio elements cannot send Authorization headers, so we fetch the audio
 * via JavaScript with proper auth and create a Blob URL for playback.
 * @param {string} entryId - Entry UUID
 * @returns {Promise<string>} Blob URL for audio playback
 */
export async function fetchAudioBlobUrl(entryId) {
    const url = `${API_BASE}/entries/${entryId}/audio`;
    const token = getToken();
    
    const response = await fetch(url, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    if (!response.ok) {
        throw new Error(`Failed to fetch audio: ${response.status}`);
    }
    
    const blob = await response.blob();
    return URL.createObjectURL(blob);
}
