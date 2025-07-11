import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { UploadedFilesProvider } from './components/UploadedFilesContext';
import { FileProvider } from './context/FileContext';

import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard/Dashboard';
import Login from './pages/Login'
import Home from './pages/Home';
import Profile from './pages/Profile';

import './styles/main.scss'; // Importa os estilos CSS
import './fonts.css'; // Importe o arquivo CSS de fontes



function App() {
  return (
    <Router>
      <UploadedFilesProvider>
        <FileProvider>
          <Navbar />
          <div className="background">
            <div className='app-wrapper'>
              <div className='content-scrollable'>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="/dashboard" element={<Dashboard />} />
              </Routes>
            </div>
            </div>
          </div>
        </FileProvider>
      </UploadedFilesProvider>
    </Router>
  );
}

export default App;



