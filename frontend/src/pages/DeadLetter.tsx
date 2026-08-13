import React, { useEffect, useState } from 'react';
import { AlertOctagon, RotateCcw, Trash2, ShieldAlert } from 'lucide-react';
import { adminApi } from '../services/api';
import { Job } from '../types';
import { StatusBadge } from '../components/StatusBadge';

export const DeadLetter: React.FC<{ refreshTrigger: number }> = ({ refreshTrigger }) => {
  const [dlqJobs, setDlqJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDLQ = async () => {
    try {
      const data = await adminApi.getDeadLetterJobs();
      setDlqJobs(data.items || []);
    } catch (e) {
      console.error("Failed to load DLQ jobs:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDLQ();
  }, [refreshTrigger]);

  const handleRetry = async (id: string) => {
    try {
      await adminApi.retryDeadLetterJob(id);
      fetchDLQ();
    } catch (e) {
      alert("Failed to retry dead-letter job.");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Permanently purge this dead-letter job from TaskFlow?")) return;
    try {
      await adminApi.deleteDeadLetterJob(id);
      fetchDLQ();
    } catch (e) {
      alert("Failed to delete dead-letter job.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center space-x-2">
            <AlertOctagon className="w-5 h-5 text-rose-500" />
            <span>Dead Letter Queue (DLQ)</span>
          </h2>
          <p className="text-xs text-slate-400">Jobs that continuously failed after exhausting max retry attempts</p>
        </div>
        <div className="px-3 py-1.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-mono font-bold">
          {dlqJobs.length} Quarantined Jobs
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-500 text-xs">Loading Dead Letter Queue...</div>
      ) : dlqJobs.length === 0 ? (
        <div className="p-10 rounded-2xl bg-dark-800/80 border border-dark-700 text-center space-y-2">
          <ShieldAlert className="w-8 h-8 text-emerald-400 mx-auto opacity-80" />
          <h3 className="font-bold text-white text-sm">Dead Letter Queue is Clean</h3>
          <p className="text-xs text-slate-400">All asynchronous worker executions are completing within normal retry limits.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {dlqJobs.map((job) => (
            <div key={job.id} className="p-5 rounded-2xl bg-dark-800/80 border border-rose-500/30 hover:border-rose-500/50 transition-all space-y-3">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div className="flex items-center space-x-3">
                  <span className="font-mono font-bold text-white text-sm">{job.id}</span>
                  <StatusBadge status={job.status} />
                  <span className="px-2 py-0.5 rounded bg-dark-900 text-slate-300 font-mono text-xs">
                    {job.job_type}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleRetry(job.id)}
                    className="flex items-center space-x-1 px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 rounded-lg text-xs font-medium transition-colors"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Re-enqueue</span>
                  </button>
                  <button
                    onClick={() => handleDelete(job.id)}
                    className="flex items-center space-x-1 px-3 py-1.5 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 rounded-lg text-xs font-medium transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Purge</span>
                  </button>
                </div>
              </div>

              {job.error_message && (
                <div className="p-3 rounded-xl bg-dark-900 border border-dark-700 text-xs font-mono text-rose-400">
                  {job.error_message}
                </div>
              )}

              <div className="text-[11px] text-slate-400 flex items-center space-x-4">
                <span>Failed Retries: {job.retry_count}/{job.max_retries}</span>
                <span>Submitted: {new Date(job.created_at).toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
