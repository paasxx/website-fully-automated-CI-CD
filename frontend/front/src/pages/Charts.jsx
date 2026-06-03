import { useState, useEffect } from 'react';
import {
    BarChart, Bar,
    LineChart, Line,
    XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import axiosInstance from '../api/axiosConfig';

// Brand colors per bank
const BANK_COLORS = {
    nubank: '#820ad1',
    inter:  '#ff7a00',
    btg:    '#4169e1',
};

const DEFAULT_COLOR = '#4caf50';

const formatCurrency = (value) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);

const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    const total = payload.reduce((s, p) => s + (p.value ?? 0), 0);
    return (
        <div className="chart-tooltip">
            <p className="chart-tooltip__label">{label}</p>
            {payload.map(p => (
                <p key={p.dataKey} className="chart-tooltip__row" style={{ color: p.color }}>
                    {p.dataKey}: {formatCurrency(p.value)}
                </p>
            ))}
            {payload.length > 1 && (
                <p className="chart-tooltip__total">Total: {formatCurrency(total)}</p>
            )}
        </div>
    );
};

const CHART_TYPES = ['bar', 'line'];

const Charts = () => {
    const [chartData, setChartData] = useState({ data: [], banks: [] });
    const [loading, setLoading] = useState(true);
    const [chartType, setChartType] = useState('bar');

    useEffect(() => {
        axiosInstance
            .get('/finances/spending-over-time/')
            .then(res => setChartData(res.data))
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    const { data, banks } = chartData;
    const total = data.reduce((sum, d) =>
        sum + banks.reduce((s, b) => s + (d[b] ?? 0), 0), 0
    );

    const sharedAxisProps = {
        tick: { fill: 'var(--text-color)', fontSize: 12 },
        axisLine: false,
        tickLine: false,
    };

    const renderBars = () => banks.map(bank => (
        <Bar
            key={bank}
            dataKey={bank}
            stackId="spending"
            fill={BANK_COLORS[bank] ?? DEFAULT_COLOR}
            radius={banks.indexOf(bank) === banks.length - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]}
        />
    ));

    const renderLines = () => banks.map(bank => (
        <Line
            key={bank}
            type="monotone"
            dataKey={bank}
            stroke={BANK_COLORS[bank] ?? DEFAULT_COLOR}
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
        />
    ));

    return (
        <div className="charts-page">
            <div className="charts-header">
                <h1>Spending Over Time</h1>
                {data.length > 0 && (
                    <p className="charts-total">
                        Total: <strong>{formatCurrency(total)}</strong>
                    </p>
                )}
                <div className="chart-type-toggle">
                    {CHART_TYPES.map(type => (
                        <button
                            key={type}
                            className={`chart-type-btn ${chartType === type ? 'chart-type-btn--active' : ''}`}
                            onClick={() => setChartType(type)}
                        >
                            {type === 'bar' ? 'Bar' : 'Line'}
                        </button>
                    ))}
                </div>
            </div>

            {loading ? (
                <p className="charts-empty">Loading...</p>
            ) : data.length === 0 ? (
                <p className="charts-empty">No data yet. Upload a statement to see your spending.</p>
            ) : (
                <div className="charts-card">
                    <ResponsiveContainer width="100%" height={360}>
                        {chartType === 'bar' ? (
                            <BarChart data={data} margin={{ top: 16, right: 24, left: 16, bottom: 8 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" opacity={0.3} />
                                <XAxis dataKey="month" {...sharedAxisProps} />
                                <YAxis tickFormatter={v => `R$${(v / 1000).toFixed(0)}k`} {...sharedAxisProps} />
                                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--border-color)', opacity: 0.15 }} />
                                <Legend wrapperStyle={{ fontSize: 12, color: 'var(--text-color)' }} />
                                {renderBars()}
                            </BarChart>
                        ) : (
                            <LineChart data={data} margin={{ top: 16, right: 24, left: 16, bottom: 8 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" opacity={0.3} />
                                <XAxis dataKey="month" {...sharedAxisProps} />
                                <YAxis tickFormatter={v => `R$${(v / 1000).toFixed(0)}k`} {...sharedAxisProps} />
                                <Tooltip content={<CustomTooltip />} />
                                <Legend wrapperStyle={{ fontSize: 12, color: 'var(--text-color)' }} />
                                {renderLines()}
                            </LineChart>
                        )}
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    );
};

export default Charts;
