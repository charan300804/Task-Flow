import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { JobSubmitModal } from './components/JobSubmitModal';
import { Dashboard } from './pages/Dashboard';
import { JobsList } from './pages/JobsList';
import { JobDetail } from './pages/JobDetail';
import { Workers } from './pages/Workers';
import { Schedules } from './pages/Schedules';
import { DeadLetter } from './pages/DeadLetter';
import { MetricsPage } from './pages/Metrics';

export const App: React.FC = () => {
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Auto-polling effect (5s interval)
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      setRefreshTrigger(prev => prev + 1);
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleManualRefresh = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <Router>
      <div className="min-h-screen bg-dark-900 text-slate-100 flex flex-col font-sans">
        <Navbar
          onOpenSubmitModal={() => setIsSubmitModalOpen(true)}
          autoRefresh={autoRefresh}
          onToggleAutoRefresh={() => setAutoRefresh(!autoRefresh)}
          onManualRefresh={handleManualRefresh}
        />

        <div className="flex flex-1">
          <Sidebar />

          <main className="flex-1 p-6 overflow-y-auto">
            <Routes>
              <Route path="/" element={<Dashboard refreshTrigger={refreshTrigger} />} />
              <Route path="/jobs" element={<JobsList refreshTrigger={refreshTrigger} />} />
              <Route path="/jobs/:id" element={<JobDetail />} />
              <Route path="/workers" element={<Workers refreshTrigger={refreshTrigger} />} />
              <Route path="/schedules" element={<Schedules refreshTrigger={refreshTrigger} />} />
              <Route path="/dead-letter" element={<DeadLetter refreshTrigger={refreshTrigger} />} />
              <Route path="/metrics" element={<MetricsPage refreshTrigger={refreshTrigger} />} />
            </Routes>
          </main>
        </div>

        {/* Global Submit Modal */}
        <JobSubmitModal
          isOpen={isSubmitModalOpen}
          onClose={() => setIsSubmitModalOpen(false)}
          onJobSubmitted={handleManualRefresh}
        />
      </div>
    </Router>
  );
};

export default App;
