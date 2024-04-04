import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useUploadedFiles } from './UploadedFilesContext';
import { FaSpinner } from 'react-icons/fa'; // Example with React Icons


const UploadCSV = () => {
    const [selectedFile, setSelectedFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const { updateUploadedFiles } = useUploadedFiles();
    const [uploadStartTime, setUploadStartTime] = useState(null);
    const [uploadTime, setUploadTime] = useState(0); // State to hold the upload time

    useEffect(() => {
        let interval;
        if (uploading) {
            interval = setInterval(() => {
                const currentTime = new Date();
                const elapsedTime = (currentTime - uploadStartTime) / 1000; // Calculate elapsed time in seconds
                setUploadTime(elapsedTime);
            }, 1000); // Update every second
        } else {
            clearInterval(interval); // Clear interval when upload is finished
        }

        return () => clearInterval(interval); // Cleanup on unmount or when uploading is finished
    }, [uploading, uploadStartTime]);

    const handleFileChange = (event) => {
        setSelectedFile(event.target.files[0]);
        setUploadStartTime(new Date());
    };

    const formatTime = (timeInSeconds) => {
        return Math.floor(timeInSeconds); // Show only seconds
    };


    const handleSubmit = async (event) => {
        event.preventDefault();

        if (selectedFile) {
            setUploading(true);
            setUploadStartTime(new Date());
            const formData = new FormData();
            formData.append('csv_file', selectedFile);

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
                    updateUploadedFiles(); // Fetch the updated list of uploaded files
                } else {
                    console.error('Failed to upload CSV file');
                }
            } catch (error) {
                console.error('Error:', error);
            } finally {
                setUploading(false);
            }
        } else {
            alert('Select a CSV file to upload');
        }
    };

    return (
        <div className="upload-form">
            <h2>Upload CSV</h2>
            <form onSubmit={handleSubmit} encType="multipart/form-data">
                <input type="file" id="csv_file" onChange={handleFileChange} accept=".csv" name="csv_file" className="file-input" />
                <label htmlFor="csv_file">Choose File</label>
                <button type="submit" disabled={uploading}>Upload</button>
                {selectedFile && <p>File: {selectedFile.name}</p>}
                {uploading && <p><FaSpinner className="spinner" /> Uploading... ({formatTime(uploadTime)} seconds)</p>}
            </form>


        </div>
    );
};

export default UploadCSV;
