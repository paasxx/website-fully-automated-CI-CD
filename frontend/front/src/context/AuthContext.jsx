import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const AuthContext = createContext();

// Reutiliza a mesma BASE_URL do axiosConfig para não duplicar
const BASE_URL = import.meta.env.REACT_APP_BACKEND_URL || '/api';

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    // loading=true enquanto verifica o token salvo — evita piscar a tela de login
    const [loading, setLoading] = useState(true);

    const logout = useCallback(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setUser(null);
    }, []);

    // Busca os dados do usuário usando um access token
    const fetchUser = useCallback(async (token) => {
        const res = await axios.get(`${BASE_URL}/auth/me/`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        setUser(res.data);
    }, []);

    // Na inicialização: se já tem token salvo, tenta restaurar a sessão
    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (!token) { setLoading(false); return; }

        fetchUser(token)
            .catch(() => logout())      // token expirado → limpa e vai para login
            .finally(() => setLoading(false));
    }, [fetchUser, logout]);

    const login = async (email, password) => {
        const res = await axios.post(`${BASE_URL}/auth/token/`, { email, password });
        localStorage.setItem('access_token', res.data.access);
        localStorage.setItem('refresh_token', res.data.refresh);
        await fetchUser(res.data.access);
        // Se fetchUser jogar erro, o login() vai propagar — o componente trata
    };

    const updateUser = useCallback((data) => setUser(data), []);

    return (
        <AuthContext.Provider value={{ user, loading, login, logout, updateUser }}>
            {children}
        </AuthContext.Provider>
    );
};
