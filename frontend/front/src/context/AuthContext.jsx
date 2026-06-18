import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axiosInstance from '../api/axiosConfig';

const AuthContext = createContext();


export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    // loading=true enquanto verifica o token salvo — evita piscar a tela de login
    const [loading, setLoading] = useState(true);
    const [sessionExpired, setSessionExpired] = useState(false);

    const logout = useCallback(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setUser(null);
    }, []);

    // Busca os dados do usuário usando um access token
    const fetchUser = useCallback(async () => {
        const res = await axiosInstance.get(`/auth/me/`);
        setUser(res.data);
    }, []);

    useEffect(() => {
        const handle = () => {
            logout();
            setSessionExpired(true);
        };
        window.addEventListener('auth:expired', handle);
        return () => window.removeEventListener('auth:expired', handle);
    }, [logout]);

    // Na inicialização: se já tem token salvo, tenta restaurar a sessão
    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (!token) { setLoading(false); return; }

        fetchUser()
            .catch(() => logout())      // token expirado → limpa e vai para login
            .finally(() => setLoading(false));
    }, [fetchUser, logout]);

    const login = async (email, password) => {
        const res = await axiosInstance.post(`/auth/token/`, { email, password });
        localStorage.setItem('access_token', res.data.access);
        localStorage.setItem('refresh_token', res.data.refresh);
        setSessionExpired(false);
        await fetchUser();
        // Se fetchUser jogar erro, o login() vai propagar — o componente trata
    };

    const updateUser = useCallback((data) => setUser(data), []);

    return (
        <AuthContext.Provider value={{ user, loading, login, logout, updateUser, sessionExpired }}>
            {children}
        </AuthContext.Provider>
    );
};
