import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { UploadedFilesProvider } from './components/Legacy/UploadedFilesContext';
import { FileProvider } from './context/FileContext';

import Navbar from './components/Navbar/Navbar';
import Dashboard from './components/Dashboard/Dashboard';
import Login from './pages/Login'
import Home from './pages/Home';
import Profile from './pages/Profile';

import './styles/main.scss'; // Importa os estilos CSS
import './fonts.css'; // Importe o arquivo CSS de fontes
import { ThemeProvider } from './context/ThemeContext';



function App() {
  return (
    <ThemeProvider>
      <Router>
        <UploadedFilesProvider>
          <FileProvider>
              <Navbar />
              <main className="app-content">
                  <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/profile" element={<Profile />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                  </Routes>
              </main>
          </FileProvider>
        </UploadedFilesProvider>
      </Router>
    </ThemeProvider>
  );
}

export default App;



