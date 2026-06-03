import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import ThemeToggleButton from './ThemeToggleButton';

const Navbar = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <nav className="navbar">
            <NavLink to="/dashboard" className="navbar-brand">FinTrack</NavLink>

            <div className="navbar-links">
                {user ? (
                    <>
                        <NavLink to="/dashboard" className="navbar-link">Dashboard</NavLink>
                        <NavLink to="/charts" className="navbar-link">Charts</NavLink>
                        <NavLink to="/profile" className="navbar-link">Profile</NavLink>
                        <button className="navbar-logout" onClick={handleLogout}>Logout</button>
                    </>
                ) : (
                    <>
                        <NavLink to="/login" className="navbar-link">Login</NavLink>
                        <NavLink to="/register" className="navbar-link">Register</NavLink>
                    </>
                )}
                <ThemeToggleButton />
            </div>
        </nav>
    );
};

export default Navbar;
