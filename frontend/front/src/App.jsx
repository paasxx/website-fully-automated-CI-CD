import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import PrivateRoute from './components/PrivateRoute';

import Navbar from './components/Navbar/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Charts from './pages/Charts';
import Profile from './pages/Profile';
import Categories from './pages/Categories';

import './styles/main.scss';
import './fonts.css';

function App() {
    return (
        <ThemeProvider>
            <AuthProvider>
                <Router>
                    <Navbar />
                    <main className="app-content">
                        <Routes>
                            <Route path="/login" element={<Login />} />
                            <Route path="/register" element={<Register />} />

                            <Route path="/dashboard" element={
                                <PrivateRoute><Dashboard /></PrivateRoute>
                            } />
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
