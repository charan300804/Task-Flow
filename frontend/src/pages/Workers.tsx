import React, { useEffect, useState } from 'react';
import { Server, Activity, ShieldCheck, AlertTriangle, Cpu, CheckCircle } from 'lucide-react';
import { workersApi } from '../services/api';
import { WorkerNode } from '../types';
import { StatusBadge } from '../components/StatusBadge';

export const Workers: React.FC<{ refreshTrigger: number }> = ({ refreshTrigger }) => {
  const [workers, setWorkers] = useState<WorkerNode[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchWorkers = async () => {
    try {
      const data = await workersApi.getWorkers();
      setWorkers(data || []);
    } catch (e) {
      console.error("Failed to load worker cluster nodes:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkers();
  }, [refreshTrigger]);

  const activeCount = workers.filter(w => ['IDLE', 'BUSY'].includes(w.status)).length;
  const unhealthyCount = workers.filter(w => w.status === 'UNHEALTHY').length;
  const totalCompleted = workers.reduce((acc, w) => acc + w.jobs_completed, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Worker Cluster Nodes</h2>
          <p className="text-xs text-slate-400">Distributed background worker daemons with heartbeat & capability matching</p>
        </div>
        <div className="flex items-center space-x-3 text-xs font-mono">
          <div className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            {activeCount} Active Nodes
          </div>
          <div className="px-3 py-1.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
            {unhealthyCount} Unhealthy
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 text-slate-500 text-xs">
          <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mr-2" />
          <span>Polling Worker Cluster Nodes...</span>
        </div>
      ) : workers.length === 0 ? (
        <div className="p-8 rounded-2xl bg-dark-800/80 border border-dark-700 text-center text-slate-500 text-xs">
          No worker instances connected. Scale up workers using <code className="text-indigo-400 font-mono">docker compose up --scale worker=3</code>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workers.map((worker) => (
            <div key={worker.id} className="p-5 rounded-2xl bg-dark-800/80 border border-dark-700/80 hover:border-dark-600 transition-all space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Server className="w-5 h-5 text-indigo-400" />
                  <span className="font-mono font-bold text-white text-sm">{worker.id}</span>
                </div>
                <StatusBadge status={worker.status} />
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex justify-between text-slate-400">
                  <span>Hostname:</span>
                  <span className="font-mono text-white">{worker.hostname}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Last Heartbeat:</span>
                  <span className="font-mono text-emerald-400">
                    {new Date(worker.last_heartbeat).toLocaleTimeString()}
                  </span>
                </div>
                {worker.current_job_id && (
                  <div className="flex justify-between text-slate-400">
                    <span>Processing Job:</span>
                    <span className="font-mono text-indigo-400">{worker.current_job_id.substring(0, 8)}...</span>
                  </div>
                )}
              </div>

              {/* Capabilities Pills */}
              <div>
                <span className="text-[11px] text-slate-500 uppercase font-semibold block mb-1.5">Capabilities</span>
                <div className="flex flex-wrap gap-1.5">
                  {worker.capabilities.map((cap, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-dark-900 border border-dark-700 text-[10px] text-indigo-300 font-mono">
                      {cap}
                    </span>
                  ))}
                </div>
              </div>

              {/* Worker Stats */}
              <div className="pt-3 border-t border-dark-700/60 grid grid-cols-2 gap-2 text-center text-xs font-mono">
                <div className="p-2 rounded-xl bg-dark-900/60">
                  <span className="text-slate-400 block text-[10px]">Completed</span>
                  <span className="text-emerald-400 font-bold">{worker.jobs_completed}</span>
                </div>
                <div className="p-2 rounded-xl bg-dark-900/60">
                  <span className="text-slate-400 block text-[10px]">Failed</span>
                  <span className="text-rose-400 font-bold">{worker.jobs_failed}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
