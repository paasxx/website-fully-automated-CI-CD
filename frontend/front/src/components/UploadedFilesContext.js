// UploadedFilesContext.js
import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios'; // Import axios to make API requests


const UploadedFilesContext = createContext();

export const useUploadedFiles = () => useContext(UploadedFilesContext);

export const UploadedFilesProvider = ({ children }) => {
    const [uploadedFiles, setUploadedFiles] = useState([]);

    const updateUploadedFiles = async () => {
        try {
            // Make an API request to fetch the uploaded files
            const response = await axios.get('http://localhost:8000/api/list-files/');
            // Update the uploadedFiles state with the fetched data
            setUploadedFiles(response.data);
        } catch (error) {
            console.error('Error fetching uploaded files:', error);
        }
    };

    // Fetch uploaded files when the component mounts
    useEffect(() => {
        updateUploadedFiles();
    }, []);

    return (
        <UploadedFilesContext.Provider value={{ uploadedFiles, updateUploadedFiles }}>
            {children}
        </UploadedFilesContext.Provider>
    );
};
