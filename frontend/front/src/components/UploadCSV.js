import React, { useState } from 'react';

const UploadCSV = () => {
    const [selectedFile, setSelectedFile] = useState(null);

    const handleFileChange = (event) => {
        setSelectedFile(event.target.files[0]);
    };

    const handleSubmit = (event) => {
        event.preventDefault();
        if (selectedFile) {
            // Lógica para enviar o arquivo para o backend
            console.log('Arquivo selecionado:', selectedFile);
        } else {
            alert('Selecione um arquivo CSV.');
        }
    };

    return (
        <div className="form-container">
            <div>
                <h2>Upload de CSV</h2>
                <form onSubmit={handleSubmit} className="upload-form">
                    <input type="file" onChange={handleFileChange} accept=".csv" />
                    <button type="submit">Enviar</button>
                </form>
            </div>

        </div>
    );
};

export default UploadCSV;
