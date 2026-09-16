import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { vi } from 'vitest';
import PrivateRoute from './PrivateRoute';
import { useAuth } from '../context/AuthContext';

// Troca o módulo inteiro por uma versão fake — PrivateRoute chama useAuth()
// e não precisamos de um AuthProvider real (nem de axios) só pra testar um if.
vi.mock('../context/AuthContext', () => ({
    useAuth: vi.fn(),
}));

// Helper: monta o cenário de rota que qualquer teste daqui precisa.
// /dashboard é a rota protegida; /login é pra onde o redirect deveria mandar.
function renderPrivateRoute() {
    render(
        <MemoryRouter initialEntries={['/dashboard']}>
            <Routes>
                <Route
                    path="/dashboard"
                    element={
                        <PrivateRoute>
                            <div>conteudo secreto</div>
                        </PrivateRoute>
                    }
                />
                <Route path="/login" element={<div>tela de login</div>} />
            </Routes>
        </MemoryRouter>
    );
}

describe('PrivateRoute', () => {
    it('redireciona para /login quando não há usuário logado', () => {
        useAuth.mockReturnValue({ user: null, loading: false });

        renderPrivateRoute();

        expect(screen.queryByText('conteudo secreto')).not.toBeInTheDocument();
        expect(screen.getByText('tela de login')).toBeInTheDocument();
    });

    it('mostra o conteúdo protegido quando há usuário logado', () => {
        useAuth.mockReturnValue({ user: { id: 1, email: 'a@a.com' }, loading: false });

        renderPrivateRoute();

        expect(screen.getByText('conteudo secreto')).toBeInTheDocument();
        expect(screen.queryByText('tela de login')).not.toBeInTheDocument();
    });

    it('mostra a tela de carregamento enquanto a sessão ainda está sendo verificada', () => {
        useAuth.mockReturnValue({ user: null, loading: true });

        renderPrivateRoute();

        expect(screen.queryByText('conteudo secreto')).not.toBeInTheDocument();
        expect(screen.queryByText('tela de login')).not.toBeInTheDocument();
        expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
});
