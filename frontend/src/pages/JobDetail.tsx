import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Clock, Server, FileText, Download, RotateCcw, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { jobsApi } from '../services/api';
import { Job } from '../types';
import { StatusBadge } from '../components/StatusBadge';

export const JobDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [job, setJob] = useState<Job | null>(null);
  const [resultData, setResultData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [loadingResult, setLoadingResult] = useState(false);

  const fetchJobDetail = async () => {
    if (!id) return;
    try {
      const data = await jobsApi.getJobDetail(id);
      setJob(data);

      if (data.status === 'SUCCESS') {
        setLoadingResult(true);
        try {
          const res = await jobsApi.getJobResult(id);
          setResultData(res);
        } catch (err) {
          console.error("Could not fetch job result output:", err);
        } finally {
          setLoadingResult(false);
        }
      }
    } catch (e) {
      console.error("Failed to load job detail:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobDetail();
  }, [id]);

  const handleRetry = async () => {
    if (!id) return;
    try {
      await jobsApi.retryJob(id);
      fetchJobDetail();
    } catch (e) {
      alert("Failed to retry job.");
    }
  };

  if (loading || !job) {
    return (
      <div className="flex items-center justify-center min-h-[50vh] text-slate-400">
        <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mr-2" />
        <span>Loading Job Details...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <Link to="/jobs" className="flex items-center space-x-2 text-slate-400 hover:text-white text-xs transition-colors">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Jobs Explorer</span>
        </Link>
        {['FAILED', 'DEAD_LETTER', 'CANCELLED'].includes(job.status) && (
          <button
            onClick={handleRetry}
            className="flex items-center space-x-2 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Re-enqueue Job Execution</span>
          </button>
        )}
      </div>

      {/* Main Header Banner */}
      <div className="p-6 rounded-2xl bg-dark-800/80 border border-dark-700/80 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-3">
              <h2 className="text-xl font-bold font-mono text-white">{job.id}</h2>
              <StatusBadge status={job.status} size="md" />
            </div>
            <p className="text-xs text-slate-400 mt-1">Submitted at {new Date(job.created_at).toLocaleString()}</p>
          </div>
          <div className="flex items-center space-x-4 text-xs font-mono">
            <div className="p-2.5 rounded-xl bg-dark-900 border border-dark-700">
              <span className="text-slate-400">Type: </span>
              <span className="text-indigo-400 font-bold">{job.job_type}</span>
            </div>
            <div className="p-2.5 rounded-xl bg-dark-900 border border-dark-700">
              <span className="text-slate-400">Priority: </span>
              <span className="text-amber-400 font-bold">P{job.priority}</span>
            </div>
            <div className="p-2.5 rounded-xl bg-dark-900 border border-dark-700">
              <span className="text-slate-400">Retries: </span>
              <span className="text-slate-200">{job.retry_count}/{job.max_retries}</span>
            </div>
          </div>
        </div>

        {/* Error Alert Banner */}
        {job.error_message && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs space-y-1">
            <div className="font-bold flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4" />
              <span>Execution Exception Details</span>
            </div>
            <pre className="font-mono text-[11px] whitespace-pre-wrap">{job.error_message}</pre>
          </div>
        )}
      </div>

      {/* Grid for Payload and Results */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Job Input Payload */}
        <div className="p-5 rounded-2xl bg-dark-800/80 border border-dark-700/80 space-y-3">
          <div className="flex items-center space-x-2">
            <FileText className="w-4 h-4 text-indigo-400" />
            <h3 className="font-bold text-white text-sm">Input Payload JSON</h3>
          </div>
          <pre className="p-4 rounded-xl bg-dark-900 font-mono text-xs text-indigo-300 border border-dark-700 overflow-x-auto">
            {JSON.stringify(job.payload, null, 2)}
          </pre>
          {job.idempotency_key && (
            <div className="text-xs text-slate-400">
              Idempotency Key: <span className="font-mono text-slate-200">{job.idempotency_key}</span>
            </div>
          )}
        </div>

        {/* Job Output Result */}
        <div className="p-5 rounded-2xl bg-dark-800/80 border border-dark-700/80 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <h3 className="font-bold text-white text-sm">Object Store Execution Result</h3>
            </div>
            {resultData?.download_url && (
              <a
                href={resultData.download_url}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-indigo-400 hover:underline flex items-center space-x-1"
              >
                <Download className="w-3.5 h-3.5" />
                <span>MinIO Artifact</span>
              </a>
            )}
          </div>
          {loadingResult ? (
            <div className="py-8 text-center text-xs text-slate-500">Fetching result artifact from MinIO...</div>
          ) : resultData ? (
            <pre className="p-4 rounded-xl bg-dark-900 font-mono text-xs text-emerald-300 border border-dark-700 overflow-x-auto max-h-64">
              {JSON.stringify(resultData, null, 2)}
            </pre>
          ) : (
            <div className="p-4 rounded-xl bg-dark-900/50 border border-dark-700 text-xs text-slate-500 text-center py-10">
              {job.status === 'SUCCESS' ? 'Result location stored in Postgres' : 'Output unavailable until job reaches SUCCESS status.'}
            </div>
          )}
        </div>
      </div>

      {/* Execution Attempts Timeline */}
      <div className="p-5 rounded-2xl bg-dark-800/80 border border-dark-700/80 space-y-4">
        <h3 className="font-bold text-white text-sm flex items-center space-x-2">
          <Clock className="w-4 h-4 text-indigo-400" />
          <span>Execution Attempt History & Audit Log</span>
        </h3>

        {!job.attempts || job.attempts.length === 0 ? (
          <div className="text-xs text-slate-500 py-4 text-center">No attempt records logged yet.</div>
        ) : (
          <div className="space-y-3">
            {job.attempts.map((attempt) => (
              <div key={attempt.id} className="p-4 rounded-xl bg-dark-900/60 border border-dark-700 flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center space-x-3">
                    <span className="font-mono text-xs font-bold text-white">Attempt #{attempt.attempt_number}</span>
                    <StatusBadge status={attempt.status} />
                    <span className="text-xs text-slate-400 font-mono">Worker: {attempt.worker_id || 'unassigned'}</span>
                  </div>
                  <div className="text-xs text-slate-400">
                    Started: {new Date(attempt.started_at).toLocaleTimeString()}
                    {attempt.completed_at && ` • Finished: ${new Date(attempt.completed_at).toLocaleTimeString()}`}
                  </div>
                </div>

                {attempt.execution_time_ms && (
                  <div className="text-right font-mono text-xs text-cyan-400 font-bold">
                    {attempt.execution_time_ms} ms
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
