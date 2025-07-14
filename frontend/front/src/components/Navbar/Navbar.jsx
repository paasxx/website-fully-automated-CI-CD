// ExampleNavbar.js

import React from 'react';
import { NavLink } from 'react-router-dom';
import ThemeToggleButton from './ThemeToggleButton';


const Navbar = () => {
    return (
        <nav className="navbar">
            <NavLink to="/" end className="navbar-brand">SmartStorage</NavLink>
            <div className="navbar-links">

            <NavLink to="/" className="navbar-link">
                Home
            </NavLink>
            
            <NavLink to="/login" className="navbar-link">
                Login
            </NavLink>
            
            <NavLink to="/profile" className="navbar-link">
                Meu Perfil
            </NavLink>
            <NavLink to="/dashboard" className="navbar-link">
                Dashboard
            </NavLink>
            <ThemeToggleButton />
        </div>
        </nav>
    );
};

export default Navbar;
