import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import PrivateRoute from './components/PrivateRoute';

import Navbar from './components/Navbar/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import Charts from './pages/Charts';
import Profile from './pages/Profile';
import Categories from './pages/Categories';

import './styles/main.scss';
import './fonts.css';

// Rendered inside Router so useNavigate is available.
// Appears as an overlay on whichever page the user is on when the session expires.
const SessionExpiredModal = () => {
    const { sessionExpired, logout } = useAuth();
    const navigate = useNavigate();

    if (!sessionExpired) return null;

    const handleSignIn = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="modal-overlay">
            <div className="modal-card">
                <div className="modal-title">Session Expired</div>
                <div className="modal-description">
                    Your session has expired. Please sign in again to continue.
                </div>
                <div className="modal-actions">
                    <button className="modal-btn modal-btn--confirm" onClick={handleSignIn}>
                        Sign in
                    </button>
                </div>
            </div>
        </div>
    );
};

function App() {
    return (
        <ThemeProvider>
            <AuthProvider>
                <Router>
                    <Navbar />
                    <SessionExpiredModal />
                    <main className="app-content">
                        <Routes>
                            <Route path="/login" element={<Login />} />
                            <Route path="/register" element={<Register />} />

                            <Route path="/dashboard" element={
                                <PrivateRoute><Dashboard /></PrivateRoute>
                            } />
                            <Route path="/transactions" element={<PrivateRoute><Transactions /></PrivateRoute>} />
                            <Route path="/categories" element={<PrivateRoute><Categories /></PrivateRoute>} />
                            <Route path="/charts" element={
                                <PrivateRoute><Charts /></PrivateRoute>
                            } />
                            <Route path="/profile" element={
                                <PrivateRoute><Profile /></PrivateRoute>
                            } />

                            <Route path="/" element={
                                <PrivateRoute><Navigate to="/dashboard" replace /></PrivateRoute>
                            } />
                        </Routes>
                    </main>
                </Router>
            </AuthProvider>
        </ThemeProvider>
    );
}

export default App;
