import { useState, useEffect } from 'react';
import {
    BarChart, Bar,
    LineChart, Line,
    PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import axiosInstance from '../api/axiosConfig';

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

const DEFAULT_COLOR = '#4caf50';
const PT_MONTHS = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
const CHART_TYPES = ['bar', 'line'];

const formatMonth = (monthStr) => {
    const [year, month] = monthStr.split('-');
    return `${PT_MONTHS[parseInt(month, 10) - 1]}/${year.slice(2)}`;
};

const formatCurrency = (value) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);

const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    const total = payload.reduce((s, p) => s + (p.value ?? 0), 0);
    return (
        <div className="chart-tooltip">
            <p className="chart-tooltip__label">{formatMonth(label)}</p>
            {payload.map(p => (
                <p key={p.dataKey} className="chart-tooltip__row" style={{ color: p.color }}>
                    {BANK_LABELS[p.dataKey] ?? p.dataKey}: {formatCurrency(p.value)}
                </p>
            ))}
            {payload.length > 1 && (
                <p className="chart-tooltip__total">Total: {formatCurrency(total)}</p>
            )}
        </div>
    );
};

const CustomPieTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const entry = payload[0];
    return (
        <div className="chart-tooltip">
            <p className="chart-tooltip__label" style={{ color: entry.payload.color }}>{entry.name}</p>
            <p className="chart-tooltip__row">{formatCurrency(entry.value)}</p>
            <p className="chart-tooltip__total">{(entry.payload.percent * 100).toFixed(1)}%</p>
        </div>
    );
};

const CustomLegend = ({ payload }) => (
    <div className="chart-legend">
        {(payload ?? []).map(entry => (
            <span key={entry.value} className="chart-legend-item">
                <span className="chart-legend-dot" style={{ background: BANK_COLORS[entry.value] ?? entry.color }} />
                {BANK_LABELS[entry.value] ?? entry.value}
            </span>
        ))}
    </div>
);

const PieLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
    if (percent < 0.04) return null;
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);
    return (
        <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" fontSize={12} fontWeight={600}>
            {`${(percent * 100).toFixed(0)}%`}
        </text>
    );
};

const Charts = () => {
    const [chartData, setChartData] = useState({ data: [], banks: [] });
    const [chartCategoryData, setChartCategoryData] = useState({ data: [], categories: [] });
    const [loading, setLoading] = useState(true);
    const [chartType, setChartType] = useState('bar');
    const [selectedMonth, setSelectedMonth] = useState(null);

    useEffect(() => {
        Promise.all([
            axiosInstance.get('/finances/spending-over-time/'),
            axiosInstance.get('/finances/spending-over-time-by-category/'),
        ])
            .then(([bankRes, categoryRes]) => {
                setChartData(bankRes.data);
                setChartCategoryData(categoryRes.data);
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    const { data, banks } = chartData;
    const { data: categoryData, categories } = chartCategoryData;

    const selectedMonthData = categoryData.find(item => item.month === selectedMonth);
    const pieChartData = selectedMonthData
        ? categories.map(item => ({
            name: item.name,
            color: item.color,
            value: selectedMonthData[item.name] ?? 0,
            percent: 0,
        }))
        : [];

    const pieTotal = pieChartData.reduce((sum, item) => sum + item.value, 0);
    const pieChartDataWithPercent = pieChartData.map(item => ({
        ...item,
        percent: pieTotal > 0 ? item.value / pieTotal : 0,
    }));

    const bankTotal = data.reduce((sum, d) =>
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

    const renderCategoryBars = () => categories.map(category => (
        <Bar
            key={category.name}
            dataKey={category.name}
            stackId="spending"
            fill={category.color}
            radius={[0, 0, 0, 0]}
        />
    ));

    return (
        <div className="charts-page">

            {/* Spending over time by bank */}
            <div className="charts-header">
                <h1>Spending Over Time</h1>
                {data.length > 0 && (
                    <p className="charts-total">Total: <strong>{formatCurrency(bankTotal)}</strong></p>
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
                <>
                    <div className="charts-card">
                        <ResponsiveContainer width="100%" height={360}>
                            {chartType === 'bar' ? (
                                <BarChart data={data} margin={{ top: 16, right: 24, left: 16, bottom: 8 }} onClick={(d) => setSelectedMonth(d.activeLabel)}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" opacity={0.3} />
                                    <XAxis dataKey="month" tickFormatter={formatMonth} {...sharedAxisProps} />
                                    <YAxis tickFormatter={v => `R$${(v / 1000).toFixed(0)}k`} {...sharedAxisProps} />
                                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--border-color)', opacity: 0.15 }} />
                                    <Legend content={<CustomLegend />} />
                                    {renderBars()}
                                </BarChart>
                            ) : (
                                <LineChart data={data} margin={{ top: 16, right: 24, left: 16, bottom: 8 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" opacity={0.3} />
                                    <XAxis dataKey="month" tickFormatter={formatMonth} {...sharedAxisProps} />
                                    <YAxis tickFormatter={v => `R$${(v / 1000).toFixed(0)}k`} {...sharedAxisProps} />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Legend content={<CustomLegend />} />
                                    {renderLines()}
                                </LineChart>
                            )}
                        </ResponsiveContainer>
                    </div>

                    {/* Category breakdown for selected month */}
                    <div className="charts-header">
                        <h1>
                            {selectedMonth
                                ? `Breakdown — ${formatMonth(selectedMonth)}`
                                : 'Breakdown por Categoria'}
                        </h1>
                        {selectedMonth && (
                            <p className="charts-total">Total: <strong>{formatCurrency(pieTotal)}</strong></p>
                        )}
                    </div>

                    {selectedMonth ? (
                        <div className="charts-card">
                            <ResponsiveContainer width="100%" height={360}>
                                <PieChart>
                                    <Pie
                                        data={pieChartDataWithPercent}
                                        dataKey="value"
                                        nameKey="name"
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={80}
                                        outerRadius={140}
                                        labelLine={false}
                                        label={PieLabel}
                                    >
                                        {pieChartDataWithPercent.map(entry => (
                                            <Cell key={entry.name} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip content={<CustomPieTooltip />} />
                                    <Legend content={<CustomLegend />} />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <p className="charts-empty">Clique em um mês no gráfico acima para ver o breakdown por categoria</p>
                    )}
                </>
            )}

            {/* Spending over time by category — WIP */}
            <div className="charts-header">
                <h1>Spending By Category</h1>
            </div>

            {loading ? (
                <p className="charts-empty">Loading...</p>
            ) : categoryData.length === 0 ? (
                <p className="charts-empty">No data yet.</p>
            ) : (
                <div className="charts-card">
                    <ResponsiveContainer width="100%" height={360}>
                        <BarChart data={categoryData} margin={{ top: 16, right: 24, left: 16, bottom: 8 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" opacity={0.3} />
                            <XAxis dataKey="month" tickFormatter={formatMonth} {...sharedAxisProps} />
                            <YAxis tickFormatter={v => `R$${(v / 1000).toFixed(0)}k`} {...sharedAxisProps} />
                            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--border-color)', opacity: 0.15 }} />
                            <Legend content={<CustomLegend />} />
                            {renderCategoryBars()}
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}

        </div>
    );
};

export default Charts;
