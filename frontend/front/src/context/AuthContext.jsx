import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axiosInstance from '../api/axiosConfig';

const AuthContext = createContext();


export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [sessionExpired, setSessionExpired] = useState(false);

    const logout = useCallback(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setUser(null);
        setSessionExpired(false);
    }, []);

    const fetchUser = useCallback(async () => {
        const res = await axiosInstance.get(`/auth/me/`);
        setUser(res.data);
    }, []);

    // Bridges axiosConfig's interceptor (plain JS, can't touch React state) to this
    // context: clears tokens and flags the session as dead when a refresh fails.
    useEffect(() => {
        const handle = () => {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            setSessionExpired(true);
        };
        window.addEventListener('auth:expired', handle);
        return () => window.removeEventListener('auth:expired', handle);
    }, []);

    // Restores the session on every fresh mount (F5, new tab, browser reopen) —
    // React state resets on reload, but a saved token survives it.
    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (!token) { setLoading(false); return; }

        fetchUser()
            .catch(() => logout())      
            .finally(() => setLoading(false));
    }, [fetchUser, logout]);
    // fetchUser and logout are stable because they're wrapped in useCallback, so this effect runs only once, 
    // but if useCallback is removed this sintax is safer than an empty dependency array.

    const login = async (email, password) => {
        const res = await axiosInstance.post(`/auth/token/`, { email, password });
        localStorage.setItem('access_token', res.data.access);
        localStorage.setItem('refresh_token', res.data.refresh);
        setSessionExpired(false);
        await fetchUser();
    };

    const updateUser = useCallback((data) => setUser(data), []);

    return (
        <AuthContext.Provider value={{ user, loading, login, logout, updateUser, sessionExpired }}>
            {children}
        </AuthContext.Provider>
    );
};
