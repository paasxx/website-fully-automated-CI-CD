const FileListCard = () => {
    return (
        <div className="dashboard-card--large">
            <h2>Transactions</h2>
            <div className="dashboard-card--large__body">
                <p style={{ opacity: 0.5 }}>No transactions yet. Upload a statement to get started.</p>
            </div>
        </div>
    );
};

export default FileListCard;
