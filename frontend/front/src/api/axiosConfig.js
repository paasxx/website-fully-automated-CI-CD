// axiosConfig.js
import axios from 'axios';

const axiosInstance = axios.create({
    baseURL: import.meta.env.REACT_APP_BACKEND_URL || '/api',
    timeout: 250000,
});

// Função para pegar o token CSRF do cookie
function getCSRFToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');

    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith(name + '=')) {
            return cookie.substring(name.length + 1);
        }
    }
    return null;
}

// Interceptor: anexa JWT + CSRF em cada requisição
axiosInstance.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
    }
    const csrfToken = getCSRFToken();
    if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
    }
    return config;
}, (error) => {
    return Promise.reject(error);
});

axiosInstance.interceptors.response.use(
    res => res,
    async err => {
        const original = err.config;
        if (err.response?.status !== 401) return Promise.reject(err);
        // A 401 from the login endpoint means bad credentials — not an expired session.
        // Let the Login page handle it (it shows "Invalid email or password").
        if (original.url?.endsWith('/auth/token/')) {
            return Promise.reject(err);
        }
        if (original.url?.includes('token/refresh')) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.dispatchEvent(new CustomEvent('auth:expired'));
            return Promise.reject(err);
        }
        if (original._retry) return Promise.reject(err);
        original._retry = true;
        const refresh = localStorage.getItem('refresh_token');
        if (!refresh) {
            window.dispatchEvent(new CustomEvent('auth:expired'));
            return Promise.reject(err);
        }
        try {
            const { data } = await axiosInstance.post('/auth/token/refresh/', { refresh });
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('refresh_token', data.refresh);
            return axiosInstance(original);
        } catch {
            window.dispatchEvent(new CustomEvent('auth:expired'));
            return Promise.reject(err);
        }
    }
);

export default axiosInstance;