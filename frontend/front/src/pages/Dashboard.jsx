import { useState, useEffect } from 'react';
import axiosInstance from '../api/axiosConfig';

const PT_MONTHS = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

const formatCurrency = (value) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);

const formatMonth = (monthStr) => {
    const [year, month] = monthStr.split('-');
    return `${PT_MONTHS[parseInt(month, 10) - 1]}/${year.slice(2)}`;
};

const AVAILABLE_MONTHS = [ '2024-03', '2026-04'];
const CURRENT_MONTH = AVAILABLE_MONTHS[AVAILABLE_MONTHS.length - 1];

const KpiCard = ({ label, value, sub, color, variation }) => (
    <div className="kpi-card">
        <p className="kpi-card__label">{label}</p>
        <p className="kpi-card__value" style={color ? { color } : {}}>{value}</p>
        {sub && <p className="kpi-card__sub">{sub}</p>}
        {variation !== undefined && (
            <span className={`kpi-card__variation ${variation > 0 ? 'kpi-card__variation--up' : 'kpi-card__variation--down'}`}>
                {variation > 0 ? '▲' : '▼'} {Math.abs(variation).toFixed(1)}% vs previous month
            </span>
        )}
    </div>
);

const KpiListCard = ({ label, items, renderName, renderValue, getColor }) => (
    <div className="kpi-card">
        <p className="kpi-card__label">{label}</p>
        <ul className="kpi-card__list">
            {items.map((item, i) => (
                <li key={i} className="kpi-card__list-item">
                    <span className="kpi-card__list-rank">{i + 1}</span>
                    <span className="kpi-card__list-name" style={getColor ? { color: getColor(item) } : {}}>
                        {renderName(item)}
                    </span>
                    <span className="kpi-card__list-value">{renderValue(item)}</span>
                </li>
            ))}
        </ul>
    </div>
);

const Dashboard = () => {
    const [month, setMonth] = useState(CURRENT_MONTH);
    const [summaryData, setSummaryData] = useState(null);
    const [loading, setLoading] = useState(true);

    const params = {
        month: month,
    };

    useEffect(() => {
        setLoading(true);
        axiosInstance.get('/finances/dashboard/', {params})
        .then(res => {
            setSummaryData(res.data);
        })
        .catch(err => {
            console.error('Error fetching dashboard data:', err);
        })
        .finally(() => {
            setLoading(false);
        });
    }, [month])  

    return (
        <div className="dashboard-page">
            <div className="dashboard-summary-card">
                <div className="dashboard-summary-card__header">
                    <h2>Monthly Summary</h2>
                    <select
                        className="tx-filter-select"
                        value={month}
                        onChange={(e) => setMonth(e.target.value)}
                    >
                        {AVAILABLE_MONTHS.map(m => (
                            <option key={m} value={m}>{formatMonth(m)}</option>
                        ))}
                    </select>
                </div>
            {loading ? <p>Loading...</p> : (
                <div className="kpi-grid">
                    <KpiCard
                        label="Total spent"
                        value={formatCurrency(summaryData?.total)}
                        variation={summaryData?.variation}
                    />
                    <KpiListCard
                        label="Top categories"
                        items={summaryData?.top_categories}
                        renderName={(item) => item.name}
                        renderValue={(item) => formatCurrency(item.total)}
                        getColor={(item) => item.color}
                    />
                    <KpiListCard
                        label="Top merchants"
                        items={summaryData?.top_merchants}
                        renderName={(item) => item.name}
                        renderValue={(item) => formatCurrency(item.total)}
                    />
                    <KpiListCard
                        label="Biggest transactions"
                        items={summaryData?.biggest_transactions}
                        renderName={(item) => item.description}
                        renderValue={(item) => formatCurrency(item.amount)}
                    />
                </div>)}
            </div>
        </div>
    );
};

export default Dashboard;
