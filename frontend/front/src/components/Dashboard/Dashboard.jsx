import React from 'react';
import UploadCard from './UploadCard';
import RecentUploadsCard from './RecentUploadsCard';
import FileListCard from './FileListCard';

const Dashboard = () => {
  return (
    <div className="dashboard-container">
      <div className="dashboard-container__left-column">
          <UploadCard />
          <RecentUploadsCard />
      </div>
      <div className="dashboard-container__right-column">
        <FileListCard />
      </div>
    </div>
  );
};

export default Dashboard;
