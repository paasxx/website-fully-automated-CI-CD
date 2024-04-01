import React from 'react';
import UploadCSV from './components/UploadCSV';
import UploadedFilesList from './components/UploadedFilesList';
import { UploadedFilesProvider } from './components/UploadedFilesContext';

import './styles.css'; // Importa os estilos CSS
import './fonts.css'; // Importe o arquivo CSS de fontes


function App() {
  return (
    <UploadedFilesProvider>
      <div className="form-container">
        <UploadCSV />
        <div >
          <h2>Uploaded Files</h2>
          <UploadedFilesList />
        </div>
      </div>
    </UploadedFilesProvider>
  );
}

export default App;
