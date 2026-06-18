import { useState, useEffect } from 'react';
import axiosInstance from '../../api/axiosConfig';

const BANK_COLORS = {
    nubank: '#820ad1',
    inter:  '#ff7a00',
    btg:    '#4169e1',
};

const BANK_LABELS = {
    nubank: 'Nubank',
    inter:  'Inter',
    btg:    'BTG',
};

const RecentUploadsCard = ({refreshKey}) => {
    const [statements, setStatements] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        axiosInstance
            .get('/import/')
            .then(res => setStatements(res.data))
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [refreshKey]);

    return (
        <div className="dashboard-card--small">
            <h2>Recent Uploads</h2>

            {loading ? (
                <p className="recent-uploads-empty">Loading...</p>
            ) : statements.length === 0 ? (
                <p className="recent-uploads-empty">No uploads yet.</p>
            ) : (
                <ul className="recent-uploads-list">
                    {statements.map(s => (
                        <li key={s.id} className="recent-uploads-row">
                            <span
                                className="recent-uploads-bank"
                                style={{
                                    color: BANK_COLORS[s.bank] ?? 'inherit',
                                    background: (BANK_COLORS[s.bank] ?? '#888') + '26',
                                }}
                            >
                                {BANK_LABELS[s.bank] ?? s.bank}
                            </span>
                            <span className="recent-uploads-filename">{s.filename}</span>
                            <span className="recent-uploads-meta">
                                {s.transaction_count} transactions · {s.uploaded_at}
                            </span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default RecentUploadsCard;
