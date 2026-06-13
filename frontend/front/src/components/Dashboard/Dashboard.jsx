import { useState } from 'react';
import UploadCard from './UploadCard';
import RecentUploadsCard from './RecentUploadsCard';
import TransactionList from './TransactionList';

const Dashboard = () => {
    // Incrementar refreshKey força o TransactionList a re-buscar os dados
    const [refreshKey, setRefreshKey] = useState(0);

    return (
        <div className="dashboard-container">
            <div className="dashboard-container__left-column">
                <UploadCard onUploadSuccess={() => setRefreshKey(k => k + 1)} />
                <RecentUploadsCard refreshKey={refreshKey} />
            </div>
            <div className="dashboard-container__right-column">
                <TransactionList refreshKey={refreshKey} />
            </div>
        </div>
    );
};

export default Dashboard;
