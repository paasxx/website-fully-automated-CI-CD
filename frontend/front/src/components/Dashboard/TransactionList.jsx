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

const formatCurrency = (amount) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Math.abs(amount));

const TransactionList = ({ refreshKey }) => {
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setLoading(true);
        setTimeout(() => {  // ← só pra testar, remove depois
            axiosInstance
                .get('/finances/transactions/')
                .then(res => setTransactions(res.data))
                .catch(console.error)
                .finally(() => setLoading(false));
        }, 500);
    }, [refreshKey]);

    return (
        <div className="dashboard-card--large">
            <h2>Transactions</h2>

            <div className="dashboard-card--large__body">
                {loading ? (
                    <div className="spinner" />
                ) : transactions.length === 0 ? (
                    <p className="transaction-empty">No transactions yet. Upload a statement to get started.</p>
                ) : (
                    <ul className="transaction-list dashboard-card--large__scrollable">
                        {transactions.map(t => (
                            <li key={t.id} className="transaction-row">
                                <span className="transaction-date">{t.date}</span>

                                <span
                                    className="transaction-bank"
                                    style={{
                                        color: BANK_COLORS[t.bank] ?? 'inherit',
                                        background: (BANK_COLORS[t.bank] ?? '#888') + '1a',
                                        border: `1px solid ${BANK_COLORS[t.bank] ?? '#888'}80`,
                                    }}
                                >
                                    {BANK_LABELS[t.bank] ?? t.bank}
                                </span>

                                <span className="transaction-description">
                                    <span>{t.description}</span>
                                    {t.is_installment && (
                                        <span className="transaction-installment">
                                            {t.installment_number}/{t.installment_total}
                                        </span>
                                    )}
                                </span>

                                <span className={`transaction-amount ${t.is_credit ? 'transaction-amount--credit' : 'transaction-amount--debit'}`}>
                                    {t.is_credit ? '+' : '-'}{formatCurrency(t.amount)}
                                </span>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
};

export default TransactionList;
