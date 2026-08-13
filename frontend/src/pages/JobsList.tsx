import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, RotateCcw, XCircle, Trash2, ChevronLeft, ChevronRight, Eye } from 'lucide-react';
import { jobsApi } from '../services/api';
import { Job, JobStatus, JobType } from '../types';
import { StatusBadge } from '../components/StatusBadge';

export const JobsList: React.FC<{ refreshTrigger: number }> = ({ refreshTrigger }) => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [loading, setLoading] = useState(true);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await jobsApi.getJobs(page, 15, statusFilter || undefined, typeFilter || undefined);
      setJobs(res.items || []);
      setTotal(res.total || 0);
      setPages(res.pages || 1);
    } catch (e) {
      console.error("Failed to load jobs:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [page, statusFilter, typeFilter, refreshTrigger]);

  const handleCancel = async (id: string) => {
    try {
      await jobsApi.cancelJob(id);
      fetchJobs();
    } catch (e) {
      alert("Failed to cancel job.");
    }
  };

  const handleRetry = async (id: string) => {
    try {
      await jobsApi.retryJob(id);
      fetchJobs();
    } catch (e) {
      alert("Failed to retry job.");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this job record?")) return;
    try {
      await jobsApi.deleteJob(id);
      fetchJobs();
    } catch (e) {
      alert("Failed to delete job.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Distributed Jobs Queue</h2>
          <p className="text-xs text-slate-400">Monitor, filter, cancel and retry active or completed workloads</p>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center space-x-3">
          {/* Status Dropdown */}
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="bg-dark-800 border border-dark-700 text-xs text-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Statuses</option>
            {['PENDING', 'QUEUED', 'RUNNING', 'SUCCESS', 'FAILED', 'RETRYING', 'CANCELLED', 'DEAD_LETTER'].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          {/* Job Type Dropdown */}
          <select
            value={typeFilter}
            onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
            className="bg-dark-800 border border-dark-700 text-xs text-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Job Types</option>
            {['GENERIC', 'PYTHON_TASK', 'ML_PREDICTION', 'DATA_PROCESSING'].map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Jobs Table */}
      <div className="rounded-2xl bg-dark-800/80 border border-dark-700/80 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-dark-900/60 border-b border-dark-700 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3.5 px-4">Job ID</th>
                <th className="py-3.5 px-4">Type</th>
                <th className="py-3.5 px-4">Priority</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4">Created At</th>
                <th className="py-3.5 px-4">Retries</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-700/50 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    <div className="inline-flex items-center space-x-2">
                      <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                      <span>Loading job queue...</span>
                    </div>
                  </td>
                </tr>
              ) : jobs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No jobs matching selected filters.
                  </td>
                </tr>
              ) : (
                jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-dark-700/30 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-medium text-white text-[11px]">
                      {job.id}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded bg-dark-700 text-slate-300 font-mono text-[11px]">
                        {job.job_type}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`font-mono font-bold ${job.priority >= 8 ? 'text-rose-400' : job.priority >= 5 ? 'text-amber-400' : 'text-slate-400'}`}>
                        P{job.priority}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={job.status} />
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 font-mono">
                      {new Date(job.created_at).toLocaleTimeString()}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-400">
                      {job.retry_count}/{job.max_retries}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <Link
                          to={`/jobs/${job.id}`}
                          className="p-1.5 text-slate-400 hover:text-white bg-dark-700/40 hover:bg-dark-700 rounded-md transition-colors"
                          title="View Details"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </Link>
                        {['PENDING', 'QUEUED'].includes(job.status) && (
                          <button
                            onClick={() => handleCancel(job.id)}
                            className="p-1.5 text-amber-400 hover:text-amber-300 bg-amber-500/10 hover:bg-amber-500/20 rounded-md transition-colors"
                            title="Cancel Job"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                          </button>
                        )}
                        {['FAILED', 'DEAD_LETTER', 'CANCELLED'].includes(job.status) && (
                          <button
                            onClick={() => handleRetry(job.id)}
                            className="p-1.5 text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/20 rounded-md transition-colors"
                            title="Retry Execution"
                          >
                            <RotateCcw className="w-3.5 h-3.5" />
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(job.id)}
                          className="p-1.5 text-rose-400 hover:text-rose-300 bg-rose-500/10 hover:bg-rose-500/20 rounded-md transition-colors"
                          title="Delete Job"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="px-4 py-3 bg-dark-900/60 border-t border-dark-700 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing Page <span className="font-bold text-white font-mono">{page}</span> of{' '}
            <span className="font-bold text-white font-mono">{pages}</span> ({total} Total Jobs)
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1.5 rounded-lg border border-dark-700 disabled:opacity-40 hover:bg-dark-700"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage(p => Math.min(pages, p + 1))}
              disabled={page === pages}
              className="p-1.5 rounded-lg border border-dark-700 disabled:opacity-40 hover:bg-dark-700"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
