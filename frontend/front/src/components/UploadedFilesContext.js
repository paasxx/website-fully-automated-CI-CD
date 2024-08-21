// UploadedFilesContext.js
import React, { createContext, useContext, useState, useEffect } from 'react';
// import axios from 'axios'; // Import axios to make API requests
import axiosInstance from './axiosConfig';


const UploadedFilesContext = createContext();

export const useUploadedFiles = () => useContext(UploadedFilesContext);

export const UploadedFilesProvider = ({ children }) => {
    const [uploadedFiles, setUploadedFiles] = useState([]);

    const updateUploadedFiles = async () => {
        try {
            // Make an API request to fetch the uploaded files
            const response = await axiosInstance.get('/list-files/');
            // Update the uploadedFiles state with the fetched data
            console.log('API Response:', response.data); // Log the API response
            setUploadedFiles(response.data);
        } catch (error) {
            console.log('Endpoint:', axiosInstance.get('/list-files/')); // Log the API response
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
