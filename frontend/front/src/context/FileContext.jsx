import { createContext, useContext, useState, useEffect } from "react";

const FileContext = createContext();

export const useFiles = () => useContext(FileContext);

export const FileProvider = ({children}) => {

    const [files, setFiles] = useState([]);

    const fetchFiles = async () => {

        const mockData = [
            {id: 1, name: 'arquivo1.csv', url: '/files/arquivo1.csv' },
            {id: 2, name: 'foto2.jpg', url: '/files/foto2.jpg'},
        ];

        await new Promise(resolve => setTimeout(resolve, 500));
        setFiles(mockData);
    };

    useEffect(() => {
        fetchFiles();
    }, []);

    const addFile = (file) => {
        setFiles(prev => [...prev, file])
    }

    return (
        <FileContext.Provider value={{files, addFile, fetchFiles}}>
            {children}
        </FileContext.Provider>
    );
};