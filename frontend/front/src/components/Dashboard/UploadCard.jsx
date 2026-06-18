import { useState, useRef } from 'react';
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
    const [showBtgModal, setShowBtgModal] = useState(false);
    const [btgPassword, setBtgPassword] = useState('');
    const formRef = useRef(null);

    const doUpload = async (password = null) => {
        setStatus('uploading');
        setErrorMsg('');

        const formData = new FormData();
        formData.append('file', file);
        formData.append('bank', bank);
        if (password) formData.append('password', password);

        try {
            const res = await axiosInstance.post('/import/upload/', formData);
            setStatus('success');
            setFile(null);
            formRef.current?.reset();
            onUploadSuccess?.(res.data);
            setTimeout(() => setStatus('idle'), 3000);
        } catch (err) {
            setStatus('error');
            setErrorMsg(err.response?.data?.error || 'Upload failed.');
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file) return;
        if (bank === 'btg') {
            setShowBtgModal(true);
            return;
        }
        await doUpload();
    };

    const handleBtgConfirm = async () => {
        setShowBtgModal(false);
        await doUpload(btgPassword);
        setBtgPassword('');
    };

    return (
        <div className="dashboard-card--small">
            <h2>Upload Statement</h2>
            <form ref={formRef} className="upload-form-inner" onSubmit={handleSubmit}>
                <div className="upload-bank-row">
                    <select
                        className="upload-select"
                        value={bank}
                        onChange={e => setBank(e.target.value)}
                    >
                        {BANKS.map(b => (
                            <option key={b.value} value={b.value}>{b.label}</option>
                        ))}
                    </select>
                    {bank === 'btg' && (
                        <span
                            className="upload-btg-info"
                            title="Faturas BTG são protegidas por senha. Você precisará informar a senha ao fazer upload (geralmente seu CPF sem pontuação)."
                        >
                            ℹ
                        </span>
                    )}
                </div>

                <label className="upload-file-label">
                    {file ? file.name : 'Choose file'}
                    <input
                        type="file"
                        accept=".csv,.xlsx"
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

            {showBtgModal && (
                <div className="modal-overlay" onClick={() => setShowBtgModal(false)}>
                    <div className="modal-card" onClick={e => e.stopPropagation()}>
                        <h3 className="modal-title">Senha da fatura BTG</h3>
                        <p className="modal-description">
                            Faturas BTG são protegidas por senha. A senha padrão é o seu CPF sem pontuação (somente números).
                        </p>
                        <div className="form-group">
                            <label>Senha</label>
                            <input
                                type="password"
                                value={btgPassword}
                                onChange={e => setBtgPassword(e.target.value)}
                                placeholder="somente números"
                                autoFocus
                                onKeyDown={e => e.key === 'Enter' && handleBtgConfirm()}
                            />
                        </div>
                        <div className="modal-actions">
                            <button
                                className="modal-btn modal-btn--cancel"
                                onClick={() => setShowBtgModal(false)}
                            >
                                Cancelar
                            </button>
                            <button
                                className="modal-btn modal-btn--confirm"
                                onClick={handleBtgConfirm}
                                disabled={!btgPassword}
                            >
                                Confirmar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default UploadCard;
