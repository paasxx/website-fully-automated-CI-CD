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

const PT_MONTHS = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

const formatDate = (dateStr) => {
    const [year, month, day] = dateStr.split('-');
    return `${day}/${month}/${year}`;
};

const formatCurrency = (amount) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Math.abs(amount));

// Extracts the ?cursor=... value from the DRF pagination next/previous URL.
const extractCursor = (url) => {
    if (!url) return null;
    try { return new URL(url).searchParams.get('cursor'); } catch { return null; }
};

const TransactionList = ({ refreshKey }) => {
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [nextCursor, setNextCursor] = useState(null);
    const [prevCursor, setPrevCursor] = useState(null);
    const [activeCursor, setActiveCursor] = useState(null);

    // Filter state
    const [searchInput, setSearchInput] = useState('');
    const [debouncedSearch, setDebouncedSearch] = useState('');
    const [bank, setBank] = useState('');
    const [isCredit, setIsCredit] = useState('');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');

    // Debounce the search field — waits 300ms after the user stops typing
    // before triggering a fetch, avoiding a request on every keystroke.
    useEffect(() => {
        const t = setTimeout(() => {
            setDebouncedSearch(searchInput);
            setActiveCursor(null); // new search always goes back to page 1
        }, 300);
        return () => clearTimeout(t);
    }, [searchInput]);

    // When refreshKey changes (new upload), reset to page 1.
    useEffect(() => { setActiveCursor(null); }, [refreshKey]);

    // Main fetch — runs whenever any filter or cursor changes.
    useEffect(() => {
        setLoading(true);

        const params = {};
        if (debouncedSearch) params.search    = debouncedSearch;
        if (bank)            params.bank       = bank;
        if (isCredit !== '') params.is_credit  = isCredit;
        if (dateFrom)        params.date_from  = dateFrom;
        if (dateTo)          params.date_to    = dateTo;
        if (activeCursor)    params.cursor     = activeCursor;

        axiosInstance
            .get('/finances/transactions/', { params })
            .then(res => {
                setTransactions(res.data.results);
                setNextCursor(extractCursor(res.data.next));
                setPrevCursor(extractCursor(res.data.previous));
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [debouncedSearch, bank, isCredit, dateFrom, dateTo, activeCursor, refreshKey]);

    const handleBankChange = (e)     => { setBank(e.target.value);     setActiveCursor(null); };
    const handleIsCreditChange = (e) => { setIsCredit(e.target.value); setActiveCursor(null); };
    const handleDateFromChange = (e) => { setDateFrom(e.target.value); setActiveCursor(null); };
    const handleDateToChange = (e)   => { setDateTo(e.target.value);   setActiveCursor(null); };

    const hasFilters = searchInput || bank || isCredit || dateFrom || dateTo;
    const clearFilters = () => {
        setSearchInput('');
        setBank('');
        setIsCredit('');
        setDateFrom('');
        setDateTo('');
        setActiveCursor(null);
    };

    return (
        <div className="dashboard-card--large">
            <div className="dashboard-card--large__header">
                <h2>Transactions</h2>
            </div>

            <div className="tx-filters">
                <div className="tx-filter-search-row">
                    <input
                        className="tx-filter-input tx-filter-search"
                        placeholder="Search by description..."
                        value={searchInput}
                        onChange={e => setSearchInput(e.target.value)}
                    />
                    {hasFilters && (
                        <button className="tx-filter-clear" onClick={clearFilters}>
                            Clear
                        </button>
                    )}
                </div>
                <div className="tx-filter-row">
                    <select className="tx-filter-select" value={bank} onChange={handleBankChange}>
                        <option value="">All banks</option>
                        <option value="nubank">Nubank</option>
                        <option value="inter">Inter</option>
                        <option value="btg">BTG</option>
                    </select>
                    <select className="tx-filter-select" value={isCredit} onChange={handleIsCreditChange}>
                        <option value="">All</option>
                        <option value="false">Expenses</option>
                        <option value="true">Credits</option>
                    </select>
                    <input
                        type="date"
                        className="tx-filter-input tx-filter-date"
                        value={dateFrom}
                        onChange={handleDateFromChange}
                        title="From date"
                    />
                    <input
                        type="date"
                        className="tx-filter-input tx-filter-date"
                        value={dateTo}
                        onChange={handleDateToChange}
                        title="To date"
                    />
                </div>
            </div>

            <div className="dashboard-card--large__body">
                {loading ? (
                    <div className="spinner" />
                ) : transactions.length === 0 ? (
                    <p className="transaction-empty">
                        {hasFilters ? 'No transactions match the filters.' : 'No transactions yet. Upload a statement to get started.'}
                    </p>
                ) : (
                    <ul className="transaction-list dashboard-card--large__scrollable">
                        {transactions.map(t => (
                            <li key={t.id} className="transaction-row">
                                <span className="transaction-date">{formatDate(t.date)}</span>

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

            {(prevCursor || nextCursor) && (
                <div className="tx-pagination">
                    <button
                        className="tx-pagination-btn"
                        disabled={!prevCursor}
                        onClick={() => setActiveCursor(prevCursor)}
                    >
                        ← Previous
                    </button>
                    <button
                        className="tx-pagination-btn"
                        disabled={!nextCursor}
                        onClick={() => setActiveCursor(nextCursor)}
                    >
                        Next →
                    </button>
                </div>
            )}
        </div>
    );
};

export default TransactionList;
