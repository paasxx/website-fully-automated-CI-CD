import React from 'react';
import UploadCSV from './components/UploadCSV';
import UploadedFilesList from './components/UploadedFilesList';
import { UploadedFilesProvider } from './components/UploadedFilesContext';
import Navbar from './components/Navbar';

import './styles/main.scss'; // Importa os estilos CSS
import './fonts.css'; // Importe o arquivo CSS de fontes


function App() {
  return (
    <div>
      <div>
        <Navbar />
      </div>
      <div className="background">
        <UploadedFilesProvider>
          <div className="background">

            <div className="card">
              {/* Upload CSV Form Component */}
              <UploadCSV />
            </div>

            <div >
              <div className="card">

                <UploadedFilesList />
              </div>
            </div>

          </div>
        </UploadedFilesProvider>
      </div>
    </div>

  );
}

export default App;



