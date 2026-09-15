// axiosConfig.js
import axios from 'axios';

// this variable tracks simultaneously requests trying to refresh the token.
let refreshPromise = null

const axiosInstance = axios.create({
    baseURL: import.meta.env.REACT_APP_BACKEND_URL || '/api',
    timeout: 250000,
});

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

        // We only care about 401 (unauthorized — expired or invalid token)
        if (err.response?.status !== 401) return Promise.reject(err);
        
        // Status is 401, so can only be a bad password.
        if (original.url?.endsWith('/auth/token/')) {
            return Promise.reject(err);
        }

        // If the 401 status came from the refresh endpoint, there is nothing more to be done, it means the refresh token is invalid or expired, so we log out the user.

        if (original.url?.includes('token/refresh')) {            
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.dispatchEvent(new CustomEvent('auth:expired'));
            return Promise.reject(err);
        }
        // Avoid looping that can occur checking _retry
        if (original._retry) return Promise.reject(err);
        original._retry = true;

        // If there is no refresh token, we can't do anything, so we log out the user.
        const refresh = localStorage.getItem('refresh_token');
        if (!refresh) {
            window.dispatchEvent(new CustomEvent('auth:expired'));
            return Promise.reject(err);
        }

        // Finally try to refresh the access token and retry the original request.
        if (!refreshPromise) {
        refreshPromise = axiosInstance.post('/auth/token/refresh/', { refresh });

          try {
            const { data } = await refreshPromise;
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('refresh_token', data.refresh);
            refreshPromise = null;
            return axiosInstance(original);
        } catch {
            window.dispatchEvent(new CustomEvent('auth:expired'));
            refreshPromise = null;
            return Promise.reject(err);
        }

        };

        // if refreshPromise is not null this request has to wait the first refresh try to finish.
        try{
            await refreshPromise;
            return axiosInstance(original);
        }
        catch{
            refreshPromise = null;
            return Promise.reject(err);
        }
        

      
    }
);

export default axiosInstance;