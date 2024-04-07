// ExampleNavbar.js

import React from 'react';

const Navbar = () => {
    return (
        <nav className="navbar">
            <a href="/" className="navbar-brand">Logo</a>
            <div className="navbar-links">
                <a href="/" className="navbar-link">Home</a>
                <a href="/about" className="navbar-link">About</a>
                <a href="/contact" className="navbar-link">Contact</a>
            </div>
        </nav>
    );
};

export default Navbar;
