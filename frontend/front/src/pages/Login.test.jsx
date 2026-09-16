import { vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import Login from './Login';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { userEvent } from '@testing-library/user-event';

vi.mock('../context/AuthContext', () => ({
    useAuth: vi.fn(),
}));

function renderLogin() {
    render(
        <MemoryRouter initialEntries={['/login']}>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/dashboard" element={<div>Dashboard</div>} />
            </Routes>
        </MemoryRouter>
    );
}

describe('Login', () => {
    it('redirects to /dashboard when user is already logged in', () => {
        useAuth.mockReturnValue({ user: 'Pedro' });

        renderLogin();

        expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    it('redirects to /dashboard when login succeeds', async () => {

        useAuth.mockReturnValue({user: undefined, login: vi.fn().mockResolvedValue()})

        renderLogin()

        await userEvent.type(screen.getByLabelText(/email/i), "tests@example.com");
        await userEvent.type(screen.getByLabelText('Password'), "password1234");
        await userEvent.click(screen.getByRole('button', {name: /sign in/i}));

        expect(await screen.findByText('Dashboard')).toBeInTheDocument();
});

    it('show message (Invalid email or password.) when login fails.', async () => {
        
        useAuth.mockReturnValue({user: undefined, login: vi.fn().mockRejectedValue(new Error('Error trying to login'))})

        renderLogin()

        await userEvent.type(screen.getByLabelText(/email/i), "tests@example.com");
        await userEvent.type(screen.getByLabelText('Password'), "password1234");
        await userEvent.click(screen.getByRole('button', {name: /sign in/i}));

        expect(await screen.findByText('Invalid email or password.')).toBeInTheDocument();



});


});




