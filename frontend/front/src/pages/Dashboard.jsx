import { useState } from 'react';

const PT_MONTHS = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

const formatCurrency = (value) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);

const formatMonth = (monthStr) => {
    const [year, month] = monthStr.split('-');
    return `${PT_MONTHS[parseInt(month, 10) - 1]}/${year.slice(2)}`;
};

const MOCK_DATA = {
    '2025-01': {
        total: 3200.00,
        variation: -8.5,
        top_categories: [
            { name: 'Food',      total: 940.00, color: '#ff5733' },
            { name: 'Transport', total: 620.00, color: '#4169e1' },
            { name: 'Health',    total: 390.00, color: '#4caf50' },
        ],
        top_merchants: [
            { name: 'iFood',      total: 520.00 },
            { name: 'Uber',       total: 310.00 },
            { name: 'Farmácia',   total: 210.00 },
        ],
        biggest_transactions: [
            { description: 'Supermarket',   amount: 430.00 },
            { description: 'Gym annual',    amount: 380.00 },
            { description: 'Dentist',       amount: 250.00 },
        ],
    },
    '2025-02': {
        total: 2900.00,
        variation: -9.4,
        top_categories: [
            { name: 'Transport', total: 780.00, color: '#4169e1' },
            { name: 'Food',      total: 650.00, color: '#ff5733' },
            { name: 'Shopping',  total: 420.00, color: '#9c27b0' },
        ],
        top_merchants: [
            { name: 'Uber',    total: 410.00 },
            { name: 'iFood',   total: 380.00 },
            { name: 'Zara',    total: 290.00 },
        ],
        biggest_transactions: [
            { description: 'Flight ticket', amount: 890.00 },
            { description: 'Hotel',         amount: 540.00 },
            { description: 'New shoes',     amount: 290.00 },
        ],
    },
    '2025-03': {
        total: 3500.00,
        variation: 12.5,
        top_categories: [
            { name: 'Food',      total: 980.00, color: '#ff5733' },
            { name: 'Tech',      total: 899.00, color: '#00bcd4' },
            { name: 'Transport', total: 420.00, color: '#4169e1' },
        ],
        top_merchants: [
            { name: 'iFood',       total: 650.00 },
            { name: 'Apple Store', total: 899.00 },
            { name: 'Uber',        total: 280.00 },
        ],
        biggest_transactions: [
            { description: 'Apple Store',  amount: 899.00 },
            { description: 'Supermarket',  amount: 520.00 },
            { description: 'iFood',        amount: 430.00 },
        ],
    },
};

const AVAILABLE_MONTHS = Object.keys(MOCK_DATA).sort();
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
    const summary = MOCK_DATA[month];

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

                <div className="kpi-grid">
                    <KpiCard
                        label="Total spent"
                        value={formatCurrency(summary.total)}
                        variation={summary.variation}
                    />
                    <KpiListCard
                        label="Top categories"
                        items={summary.top_categories}
                        renderName={(item) => item.name}
                        renderValue={(item) => formatCurrency(item.total)}
                        getColor={(item) => item.color}
                    />
                    <KpiListCard
                        label="Top merchants"
                        items={summary.top_merchants}
                        renderName={(item) => item.name}
                        renderValue={(item) => formatCurrency(item.total)}
                    />
                    <KpiListCard
                        label="Biggest transactions"
                        items={summary.biggest_transactions}
                        renderName={(item) => item.description}
                        renderValue={(item) => formatCurrency(item.amount)}
                    />
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
