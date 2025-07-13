import React from 'react';
import { useFiles } from '../../context/FileContext';

const FileListCard = () => {
    const {files, addFile} = useFiles();

    return (

            <div className='dashboard-card--large'>
                <h2> Arquivos disponíveis:</h2>
                <div className='dashboard-card--large__body'>
                    <ul className='dashboard-card--large__scrollable'>
                        {files.map(file => (
                            <li key={file.id}>
                                <p>{file.name}</p>
                            </li>
                        ))}
                    </ul>
                </div>
                
                <div className='dashboard-card--large__footer'>
                    <button  className = 'dashboard-button-list' onClick={() => addFile({id: 2, name: 'foto2.jpg', url: '/files/foto2.jpg'})}>Add File</button>

                </div>
                     
            </div>
        
    );
};

export default FileListCard;
