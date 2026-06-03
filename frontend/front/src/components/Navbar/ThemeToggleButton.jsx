import React from 'react';
import { useTheme } from '../../context/ThemeContext';

const ThemeToggleButton = () => {

const { theme, toggleTheme } = useTheme();

return (

<button onClick={toggleTheme} className='theme-toggle-button'>
      {theme === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode'}
</button>
);

};

export default ThemeToggleButton;