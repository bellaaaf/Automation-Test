// frontend/api_config.js
// Konfigurasi URL API Backend
const API_CONFIG = {
    BASE_URL: 'http://127.0.0.1:8000/api',
    ENDPOINTS: {
        TASKS: '/tasks'
    }
};

// Helper function untuk mendapatkan full URL
function apiUrl(endpoint) {
    return `${API_CONFIG.BASE_URL}${endpoint}`;
}