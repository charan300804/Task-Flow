import React, { useEffect, useState } from 'react';
import { Calendar, Plus, Trash2, Clock, Play, ToggleLeft, ToggleRight, X } from 'lucide-react';
import { schedulesApi } from '../services/api';
import { Schedule, JobType } from '../types';

export const Schedules: React.FC<{ refreshTrigger: number }> = ({ refreshTrigger }) => {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // New Schedule Form State
  const [jobType, setJobType] = useState<JobType>('ML_PREDICTION');
  const [cronExpr, setCronExpr] = useState('0 */6 * * *');
  const [priority, setPriority] = useState(5);
  const [creating, setCreating] = useState(false);

  const fetchSchedules = async () => {
    try {
      const data = await schedulesApi.getSchedules();
      setSchedules(data || []);
    } catch (e) {
      console.error("Failed to load cron schedules:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchedules();
  }, [refreshTrigger]);

  const handleToggle = async (sched: Schedule) => {
    try {
      await schedulesApi.updateSchedule(sched.id, { enabled: !sched.enabled });
      fetchSchedules();
    } catch (e) {
      alert("Failed to update schedule status.");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this schedule?")) return;
    try {
      await schedulesApi.deleteSchedule(id);
      fetchSchedules();
    } catch (e) {
      alert("Failed to delete schedule.");
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await schedulesApi.createSchedule({
        job_type: jobType,
        cron_expression: cronExpr,
        payload: { scheduled_by: 'CronEngine' },
        priority,
        enabled: true
      });
      setIsModalOpen(false);
      fetchSchedules();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Invalid schedule configuration.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Recurring Job Schedules (Cron Engine)</h2>
          <p className="text-xs text-slate-400">Automated periodic workload triggers using standard cron syntax</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium transition-all shadow-lg shadow-indigo-600/20"
        >
          <Plus className="w-4 h-4" />
          <span>New Cron Schedule</span>
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-500 text-xs">Loading schedules...</div>
      ) : schedules.length === 0 ? (
        <div className="p-8 rounded-2xl bg-dark-800/80 border border-dark-700 text-center text-slate-500 text-xs">
          No active recurring schedules. Click "New Cron Schedule" to configure automated background jobs.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {schedules.map((sched) => (
            <div key={sched.id} className="p-5 rounded-2xl bg-dark-800/80 border border-dark-700/80 hover:border-dark-600 transition-all flex items-center justify-between">
              <div className="space-y-2">
                <div className="flex items-center space-x-3">
                  <span className="px-2.5 py-1 rounded bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-mono text-xs font-bold">
                    {sched.cron_expression}
                  </span>
                  <span className="text-xs font-semibold text-white font-mono">{sched.job_type}</span>
                </div>
                <div className="text-xs text-slate-400 space-y-1">
                  <div>Next Run: <span className="text-slate-200 font-mono">{sched.next_run_at ? new Date(sched.next_run_at).toLocaleString() : 'Pending'}</span></div>
                  <div>Last Run: <span className="text-slate-400 font-mono">{sched.last_run_at ? new Date(sched.last_run_at).toLocaleString() : 'Never'}</span></div>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={() => handleToggle(sched)}
                  className={`flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    sched.enabled ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-slate-700 text-slate-400'
                  }`}
                >
                  {sched.enabled ? 'ACTIVE' : 'DISABLED'}
                </button>
                <button
                  onClick={() => handleDelete(sched.id)}
                  className="p-1.5 text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-dark-800 border border-dark-700 rounded-2xl w-full max-w-md p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-dark-700 pb-3">
              <h3 className="font-bold text-white text-base">Configure Recurring Cron Schedule</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Workload Type</label>
                <select
                  value={jobType}
                  onChange={(e) => setJobType(e.target.value as JobType)}
                  className="w-full bg-dark-900 border border-dark-700 rounded-lg p-2.5 text-white"
                >
                  <option value="ML_PREDICTION">ML Prediction</option>
                  <option value="GENERIC">Sleep Task</option>
                  <option value="PYTHON_TASK">CPU Prime Task</option>
                  <option value="DATA_PROCESSING">Data Transformation</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Cron Expression</label>
                <input
                  type="text"
                  value={cronExpr}
                  onChange={(e) => setCronExpr(e.target.value)}
                  placeholder="e.g. 0 */6 * * *"
                  className="w-full bg-dark-900 border border-dark-700 rounded-lg p-2.5 text-white font-mono"
                  required
                />
                <span className="text-[10px] text-slate-500 block mt-1">Examples: `*/5 * * * *` (Every 5 mins), `0 * * * *` (Hourly)</span>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Priority (1-10)</label>
                <input
                  type="number"
                  value={priority}
                  onChange={(e) => setPriority(Number(e.target.value))}
                  className="w-full bg-dark-900 border border-dark-700 rounded-lg p-2.5 text-white"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-dark-700">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium"
                >
                  {creating ? 'Saving...' : 'Create Schedule'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
