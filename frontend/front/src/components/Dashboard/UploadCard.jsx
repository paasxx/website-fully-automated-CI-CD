import { useState, useRef } from 'react';
import { createPortal } from 'react-dom';
import axiosInstance from '../../api/axiosConfig';

const BANKS = [
    { value: 'nubank', label: 'Nubank' },
    { value: 'inter',  label: 'Inter'  },
    { value: 'btg',    label: 'BTG'    },
];

// Banks that require a password on upload, with UI copy per bank.
const BANK_PASSWORD_CONFIG = {
    btg: {
        title:       'Senha da fatura BTG',
        description: 'Faturas BTG são exportadas como XLSX protegido por senha. A senha padrão é o seu CPF sem pontuação (somente números).',
        placeholder: 'CPF sem pontuação',
        infoTip:     'Arquivo XLSX protegido — senha: CPF sem pontuação.',
    },
    inter: {
        title:       'Senha da fatura Inter',
        description: 'Faturas Inter em PDF são protegidas por senha. Informe os 6 primeiros dígitos do seu CPF.',
        placeholder: '6 primeiros dígitos do CPF',
        infoTip:     'Arquivo PDF protegido — senha: 6 primeiros dígitos do CPF.',
    },
};

// Tooltip rendered into document.body via portal so card overflow never clips it.
const BankInfoTooltip = ({ tip, anchorRef }) => {
    const [visible, setVisible] = useState(false);
    const [pos, setPos] = useState({ top: 0, left: 0 });

    const show = () => {
        if (anchorRef.current) {
            const r = anchorRef.current.getBoundingClientRect();
            setPos({ top: r.bottom + 8, left: r.right - 210 });
        }
        setVisible(true);
    };

    return (
        <>
            <span
                ref={anchorRef}
                className="upload-btg-info"
                aria-label="info"
                onMouseEnter={show}
                onMouseLeave={() => setVisible(false)}
            >
                i
            </span>
            {visible && createPortal(
                <div className="upload-btg-tooltip" style={{ top: pos.top, left: pos.left }}>
                    {tip}
                </div>,
                document.body
            )}
        </>
    );
};

const UploadCard = ({ onUploadSuccess }) => {
    const [bank, setBank]               = useState('nubank');
    const [file, setFile]               = useState(null);
    const [status, setStatus]           = useState('idle'); // idle | uploading | success | error
    const [errorMsg, setErrorMsg]       = useState('');
    const [showModal, setShowModal]     = useState(false);
    const [password, setPassword]       = useState('');
    const formRef    = useRef(null);
    const infoRef    = useRef(null);

    const passwordConfig = BANK_PASSWORD_CONFIG[bank];

    const doUpload = async (pwd = null) => {
        setStatus('uploading');
        setErrorMsg('');

        const formData = new FormData();
        formData.append('file', file);
        formData.append('bank', bank);
        if (pwd) formData.append('password', pwd);

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
            setTimeout(() => setStatus('idle'), 6000);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file) return;
        if (passwordConfig) {
            setShowModal(true);
            return;
        }
        await doUpload();
    };

    const handleConfirm = async () => {
        setShowModal(false);
        await doUpload(password);
        setPassword('');
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
                    {passwordConfig && (
                        <BankInfoTooltip tip={passwordConfig.infoTip} anchorRef={infoRef} />
                    )}
                </div>

                <label className="upload-file-label">
                    {file ? file.name : 'Choose file'}
                    <input
                        type="file"
                        accept=".csv,.xlsx,.pdf"
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

            {showModal && passwordConfig && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-card" onClick={e => e.stopPropagation()}>
                        <h3 className="modal-title">{passwordConfig.title}</h3>
                        <p className="modal-description">{passwordConfig.description}</p>
                        <div className="form-group">
                            <label>Senha</label>
                            <input
                                type="password"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                placeholder={passwordConfig.placeholder}
                                autoFocus
                                onKeyDown={e => e.key === 'Enter' && handleConfirm()}
                            />
                        </div>
                        <div className="modal-actions">
                            <button
                                className="modal-btn modal-btn--cancel"
                                onClick={() => setShowModal(false)}
                            >
                                Cancelar
                            </button>
                            <button
                                className="modal-btn modal-btn--confirm"
                                onClick={handleConfirm}
                                disabled={!password}
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
