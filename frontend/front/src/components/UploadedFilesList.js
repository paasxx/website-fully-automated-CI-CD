import React from 'react';
import { useUploadedFiles } from './UploadedFilesContext';

const UploadedFilesList = () => {
    const { uploadedFiles } = useUploadedFiles();



    return (
        <div className="uploaded-files-container">

            <ul>
                {uploadedFiles.map((file, index) => (
                    <li key={index} className='file-info'>
                        <span >{file.nome}</span> {/* Display file name */}
                        <span >{file.data_envio}</span> {/* Display upload date */}
                    </li>


                ))}
            </ul>
        </div>
    );
};

export default UploadedFilesList;
