import React from 'react';
import UploadCSV from './components/UploadCSV';

import './styles.css'; // Importa os estilos CSS

function UploadFile() {
  return (
    <div className="form-container">
      <UploadCSV />
    </div>
  );
}

export default UploadFile;
