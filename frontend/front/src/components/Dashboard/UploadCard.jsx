import { useState } from 'react';
import axiosInstance from '../../api/axiosConfig';

const BANKS = [
    { value: 'nubank', label: 'Nubank' },
    { value: 'inter', label: 'Inter' },
    { value: 'btg', label: 'BTG' },
];

const UploadCard = ({ onUploadSuccess }) => {
    const [bank, setBank] = useState('nubank');
    const [file, setFile] = useState(null);
    const [status, setStatus] = useState('idle'); // idle | uploading | success | error
    const [errorMsg, setErrorMsg] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file) return;

        setStatus('uploading');
        setErrorMsg('');

        const formData = new FormData();
        formData.append('file', file);
        formData.append('bank', bank);

        try {
            const res = await axiosInstance.post('/import/upload/', formData);
            setStatus('success');
            setFile(null);
            e.target.reset(); // clears the file input visually
            onUploadSuccess?.(res.data);
            setTimeout(() => setStatus('idle'), 3000);
        } catch (err) {
            setStatus('error');
            setErrorMsg(err.response?.data?.error || 'Upload failed.');
        }
    };

    return (
        <div className="dashboard-card--small">
            <h2>Upload Statement</h2>
            <form className="upload-form-inner" onSubmit={handleSubmit}>
                <select
                    className="upload-select"
                    value={bank}
                    onChange={e => setBank(e.target.value)}
                >
                    {BANKS.map(b => (
                        <option key={b.value} value={b.value}>{b.label}</option>
                    ))}
                </select>

                <label className="upload-file-label">
                    {file ? file.name : 'Choose CSV file'}
                    <input
                        type="file"
                        accept=".csv"
                        onChange={e => setFile(e.target.files[0] || null)}
                        hidden
                    />
                </label>

                <button
                    type="submit"
                    className="dashboard-button-upload"
                    disabled={!file || status === 'uploading'}
                >
                    {status === 'uploading' ? 'Uploading...' : 'Upload'}
                </button>

                {status === 'success' && (
                    <p className="upload-status upload-status--success">Imported successfully</p>
                )}
                {status === 'error' && (
                    <p className="upload-status upload-status--error">{errorMsg}</p>
                )}
            </form>
        </div>
    );
};

export default UploadCard;
