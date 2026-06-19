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

const PAGE_SIZE = 25; // must match backend TransactionPagePagination.page_size

const formatDate = (dateStr) => {
    const [year, month, day] = dateStr.split('-');
    return `${day}/${month}/${year}`;
};

const formatCurrency = (amount) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Math.abs(amount));

// Returns page numbers to display, inserting null as ellipsis placeholder.
// E.g. for 10 pages at page 6: [1, null, 4, 5, 6, 7, 8, null, 10]
const buildPageItems = (currentPage, totalPages) => {
    const pages = new Set([1, totalPages]);
    for (let i = Math.max(2, currentPage - 2); i <= Math.min(totalPages - 1, currentPage + 2); i++) {
        pages.add(i);
    }
    const sorted = [...pages].sort((a, b) => a - b);
    const items = [];
    let prev = 0;
    for (const p of sorted) {
        if (p - prev > 1) items.push(null); // null = ellipsis
        items.push(p);
        prev = p;
    }
    return items;
};

const TransactionList = ({ refreshKey }) => {
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [count, setCount] = useState(0);
    const [currentPage, setCurrentPage] = useState(1);

    // Filter state
    const [searchInput, setSearchInput] = useState('');
    const [debouncedSearch, setDebouncedSearch] = useState('');
    const [bank, setBank] = useState('');
    const [isCredit, setIsCredit] = useState('');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');
    const [category, setCategory] = useState('');
    const [categories, setCategories] = useState([]);

    useEffect(() => {
        axiosInstance.get('/finances/categories/').then(res => setCategories(res.data));
    }, []);

    // Debounce search — waits 300ms after user stops typing before fetching
    useEffect(() => {
        const t = setTimeout(() => {
            setDebouncedSearch(searchInput);
            setCurrentPage(1);
        }, 300);
        return () => clearTimeout(t);
    }, [searchInput]);

    // New upload → reset to page 1
    useEffect(() => { setCurrentPage(1); }, [refreshKey]);

    // Main fetch
    useEffect(() => {
        setLoading(true);

        const params = { page: currentPage };
        if (debouncedSearch) params.search    = debouncedSearch;
        if (bank)            params.bank       = bank;
        if (isCredit !== '') params.is_credit  = isCredit;
        if (dateFrom)        params.date_from  = dateFrom;
        if (dateTo)          params.date_to    = dateTo;
        if (category)        params.category   = category;

        axiosInstance
            .get('/finances/transactions/', { params })
            .then(res => {
                setTransactions(res.data.results);
                setCount(res.data.count);
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [debouncedSearch, bank, isCredit, dateFrom, dateTo, category, currentPage, refreshKey]);

    const goToPage    = (p) => setCurrentPage(p);
    const handleBank  = (e) => { setBank(e.target.value);     setCurrentPage(1); };
    const handleType  = (e) => { setIsCredit(e.target.value); setCurrentPage(1); };
    const handleFrom  = (e) => { setDateFrom(e.target.value); setCurrentPage(1); };
    const handleTo    = (e) => { setDateTo(e.target.value);   setCurrentPage(1); };
    const handleCategory = (e) => { setCategory(e.target.value); setCurrentPage(1); };

    const hasFilters  = searchInput || bank || isCredit || dateFrom || dateTo || category;
    const clearFilters = () => {
        setSearchInput('');
        setBank('');
        setIsCredit('');
        setDateFrom('');
        setDateTo('');
        setCategory('');
        setCurrentPage(1);
    };

    const totalPages = Math.ceil(count / PAGE_SIZE);
    const pageItems  = totalPages > 1 ? buildPageItems(currentPage, totalPages) : [];

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
                        <button className="tx-filter-clear" onClick={clearFilters}>Clear</button>
                    )}
                </div>
                <div className="tx-filter-row">
                    <select className="tx-filter-select" value={bank} onChange={handleBank}>
                        <option value="">All banks</option>
                        <option value="nubank">Nubank</option>
                        <option value="inter">Inter</option>
                        <option value="btg">BTG</option>
                    </select>
                    <select className="tx-filter-select" value={isCredit} onChange={handleType}>
                        <option value="">All</option>
                        <option value="false">Expenses</option>
                        <option value="true">Credits</option>
                    </select>
                    <input type="date" className="tx-filter-input tx-filter-date" value={dateFrom} onChange={handleFrom} title="From" />
                    <input type="date" className="tx-filter-input tx-filter-date" value={dateTo}   onChange={handleTo}   title="To" />
                    <select className="tx-filter-select" value={category} onChange={handleCategory}>
                        <option value="">All categories</option>
                        {categories.map(c => (
                            <option key={c.id} value={c.id}>
                                {c.name}
                            </option>
                        ))}
                    </select>   
                </div>
            </div>

            <div className="dashboard-card--large__body">
                {/* First load: blank spinner (no previous content to show) */}
                {loading && transactions.length === 0 ? (
                    <div className="spinner" />
                ) : (
                    <>
                        {/* Subsequent loads: overlay on top of existing list */}
                        {loading && (
                            <div className="tx-loading-overlay">
                                <div className="spinner" />
                            </div>
                        )}

                        {transactions.length === 0 ? (
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

                                        {t.category && (
                                            <span
                                                className="transaction-category"
                                                style={{
                                                    color: t.category.color,
                                                    background: t.category.color + '1a',
                                                    border: `1px solid ${t.category.color}80`,
                                                }}
                                            >
                                                {t.category.name}
                                            </span>
                                        )}

                                        <span className={`transaction-amount ${t.is_credit ? 'transaction-amount--credit' : 'transaction-amount--debit'}`}>
                                            {t.is_credit ? '+' : '-'}{formatCurrency(t.amount)}
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </>
                )}
            </div>

            {totalPages > 1 && (
                <div className="tx-pagination">
                    <button
                        className="tx-pagination-btn"
                        disabled={currentPage === 1}
                        onClick={() => goToPage(currentPage - 1)}
                    >
                        ←
                    </button>

                    {pageItems.map((item, i) =>
                        item === null ? (
                            <span key={`ellipsis-${i}`} className="tx-pagination-ellipsis">…</span>
                        ) : (
                            <button
                                key={item}
                                className={`tx-pagination-btn ${item === currentPage ? 'tx-pagination-btn--active' : ''}`}
                                onClick={() => goToPage(item)}
                            >
                                {item}
                            </button>
                        )
                    )}

                    <button
                        className="tx-pagination-btn"
                        disabled={currentPage === totalPages}
                        onClick={() => goToPage(currentPage + 1)}
                    >
                        →
                    </button>
                </div>
            )}
        </div>
    );
};

export default TransactionList;
