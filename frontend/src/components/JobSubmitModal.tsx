import React, { useState } from 'react';
import { X, Play, Brain, Cpu, Clock, Layers } from 'lucide-react';
import { JobCreate, JobType } from '../types';
import { jobsApi } from '../services/api';

interface JobSubmitModalProps {
  isOpen: boolean;
  onClose: () => void;
  onJobSubmitted: () => void;
}

export const JobSubmitModal: React.FC<JobSubmitModalProps> = ({
  isOpen,
  onClose,
  onJobSubmitted,
}) => {
  const [jobType, setJobType] = useState<JobType>('ML_PREDICTION');
  const [priority, setPriority] = useState<number>(5);
  const [maxRetries, setMaxRetries] = useState<number>(3);
  const [timeoutSeconds, setTimeoutSeconds] = useState<number>(300);
  const [idempotencyKey, setIdempotencyKey] = useState<str>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Custom task parameters based on jobType
  const [datasetSize, setDatasetSize] = useState<number>(1200);
  const [numTrees, setNumTrees] = useState<number>(50);
  const [sleepDuration, setSleepDuration] = useState<number>(5);
  const [primeLimit, setPrimeLimit] = useState<number>(25000);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    let payload: Record<string, any> = {};
    if (jobType === 'ML_PREDICTION') {
      payload = { dataset_size: datasetSize, num_trees: numTrees, model: 'RandomForestRegressor' };
    } else if (jobType === 'GENERIC') {
      payload = { duration_seconds: sleepDuration };
    } else if (jobType === 'PYTHON_TASK') {
      payload = { limit: primeLimit, task: 'cpu_prime' };
    } else {
      payload = { items_count: 5000 };
    }

    try {
      const jobData: JobCreate = {
        job_type: jobType,
        priority: Number(priority),
        max_retries: Number(maxRetries),
        timeout_seconds: Number(timeoutSeconds),
        payload
      };

      await jobsApi.submitJob(jobData, idempotencyKey || undefined);
      onJobSubmitted();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit job. Check server connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-dark-800 border border-dark-700 rounded-2xl w-full max-w-xl overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-200">
        <div className="px-6 py-4 border-b border-dark-700 flex items-center justify-between bg-dark-900/50">
          <div className="flex items-center space-x-2">
            <Play className="w-5 h-5 text-indigo-400" />
            <h2 className="text-lg font-bold text-white">Submit New Asynchronous Job</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
              {error}
            </div>
          )}

          {/* Job Type Selector */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Select Workload Type
            </label>
            <div className="grid grid-cols-2 gap-3">
              {[
                { type: 'ML_PREDICTION', label: 'ML Prediction', icon: Brain, desc: 'RandomForest Housing Model' },
                { type: 'GENERIC', label: 'Sleep Task', icon: Clock, desc: 'Background I/O Simulation' },
                { type: 'PYTHON_TASK', label: 'CPU Prime Task', icon: Cpu, desc: 'Math Intensive Computation' },
                { type: 'DATA_PROCESSING', label: 'Data Transform', icon: Layers, desc: 'Tabular Data Aggregations' },
              ].map((item) => (
                <button
                  type="button"
                  key={item.type}
                  onClick={() => setJobType(item.type as JobType)}
                  className={`p-3 rounded-xl border text-left transition-all flex flex-col justify-between ${
                    jobType === item.type
                      ? 'bg-indigo-600/15 border-indigo-500 text-indigo-300 ring-1 ring-indigo-500'
                      : 'bg-dark-900/60 border-dark-700 hover:border-slate-600 text-slate-300'
                  }`}
                >
                  <div className="flex items-center space-x-2 font-medium text-sm">
                    <item.icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </div>
                  <span className="text-[11px] text-slate-400 mt-1">{item.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Task Specific Fields */}
          {jobType === 'ML_PREDICTION' && (
            <div className="grid grid-cols-2 gap-4 p-4 rounded-xl bg-dark-900/50 border border-dark-700">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Dataset Sample Size</label>
                <input
                  type="number"
                  value={datasetSize}
                  onChange={(e) => setDatasetSize(Number(e.target.value))}
                  className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Random Forest Trees</label>
                <input
                  type="number"
                  value={numTrees}
                  onChange={(e) => setNumTrees(Number(e.target.value))}
                  className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
          )}

          {jobType === 'GENERIC' && (
            <div className="p-4 rounded-xl bg-dark-900/50 border border-dark-700">
              <label className="block text-xs text-slate-400 mb-1">Sleep Duration (Seconds)</label>
              <input
                type="number"
                value={sleepDuration}
                onChange={(e) => setSleepDuration(Number(e.target.value))}
                className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          )}

          {jobType === 'PYTHON_TASK' && (
            <div className="p-4 rounded-xl bg-dark-900/50 border border-dark-700">
              <label className="block text-xs text-slate-400 mb-1">Prime Search Upper Bound Limit</label>
              <input
                type="number"
                value={primeLimit}
                onChange={(e) => setPrimeLimit(Number(e.target.value))}
                className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          )}

          {/* Job Priority & Parameters */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Priority (1-10)</label>
              <select
                value={priority}
                onChange={(e) => setPriority(Number(e.target.value))}
                className="w-full bg-dark-900 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
              >
                {[1,2,3,4,5,6,7,8,9,10].map(p => (
                  <option key={p} value={p}>{p} {p >= 9 ? '(Critical)' : p >= 7 ? '(High)' : p >= 4 ? '(Default)' : '(Low)'}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Max Retries</label>
              <input
                type="number"
                value={maxRetries}
                onChange={(e) => setMaxRetries(Number(e.target.value))}
                className="w-full bg-dark-900 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Timeout (Sec)</label>
              <input
                type="number"
                value={timeoutSeconds}
                onChange={(e) => setTimeoutSeconds(Number(e.target.value))}
                className="w-full bg-dark-900 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1">Idempotency Key (Optional)</label>
            <input
              type="text"
              placeholder="e.g., req-uuid-12345"
              value={idempotencyKey}
              onChange={(e) => setIdempotencyKey(e.target.value)}
              className="w-full bg-dark-900 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white font-mono placeholder:text-slate-600 focus:outline-none"
            />
          </div>

          {/* Submit Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-dark-700">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-dark-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-all shadow-lg shadow-indigo-600/30 flex items-center space-x-2"
            >
              {loading && <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />}
              <span>{loading ? 'Submitting...' : 'Enqueue Job'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
