import React, { useState } from 'react';
import axios from 'axios';

const UploadCSV = () => {
    const [selectedFile, setSelectedFile] = useState(null);

    const handleFileChange = (event) => {
        setSelectedFile(event.target.files[0]);
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (selectedFile) {
            const formData = new FormData();
            formData.append('csv_file', selectedFile);

            console.log('FormData:', formData); // Log FormData object


            try {
                const response = await axios.post('http://localhost:8000/api/upload-csv/', formData, {
                    headers: {
                        "Content-Type": "multipart/form-data",
                    },
                });
                console.log('Response:', response.data);
                if (response.status === 200) {
                    console.log('CSV file uploaded successfully');
                    await axios.post('http://localhost:8000/api/save-file-name/', { nome_arquivo: selectedFile.name });
                    console.log('File name saved successfully');
                } else {
                    console.error('Failed to upload CSV file');
                }
            } catch (error) {
                console.error('Error:', error);
            }
        } else {
            alert('Select a CSV file to upload');
        }
    };

    return (
        <div>
            <h2>Upload CSV</h2>
            <form onSubmit={handleSubmit} className="upload-form" encType="multipart/form-data">
                <input type="file" onChange={handleFileChange} accept=".csv" name="csv_file" />
                <button type="submit">Upload</button>
            </form>

        </div>
    );
};

export default UploadCSV;
