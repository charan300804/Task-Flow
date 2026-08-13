import React, { useEffect, useState } from 'react';
import { 
  Activity, CheckCircle2, XCircle, Clock, Server, AlertTriangle, 
  TrendingUp, ArrowUpRight, Zap, RefreshCw 
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell 
} from 'recharts';
import { metricsApi, jobsApi, workersApi } from '../services/api';
import { SystemMetricsResponse, Job, WorkerNode } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { Link } from 'react_router_dom';

const STATUS_COLORS: Record<string, string> = {
  SUCCESS: '#10B981',
  RUNNING: '#6366F1',
  QUEUED: '#F59E0B',
  PENDING: '#EC4899',
  FAILED: '#EF4444',
  DEAD_LETTER: '#991B1B',
  CANCELLED: '#64748B'
};

export const Dashboard: React.FC<{ refreshTrigger: number }> = ({ refreshTrigger }) => {
  const [metrics, setMetrics] = useState<SystemMetricsResponse | null>(null);
  const [recentJobs, setRecentJobs] = useState<Job[]>([]);
  const [workers, setWorkers] = useState<WorkerNode[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [m, j, w] = await Promise.all([
        metricsApi.getOverviewMetrics(),
        jobsApi.getJobs(1, 6),
        workersApi.getWorkers()
      ]);
      setMetrics(m);
      setRecentJobs(j.items || []);
      setWorkers(w || []);
    } catch (e) {
      console.error("Error loading dashboard data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [refreshTrigger]);

  if (loading || !metrics) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center space-x-3 text-slate-400">
          <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <span className="font-medium">Connecting to TaskFlow Cluster...</span>
        </div>
      </div>
    );
  }

  const { overview, status_distribution, throughput_history } = metrics;

  const statCards = [
    { title: 'Total Processed Jobs', val: overview.total_jobs, icon: Activity, color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
    { title: 'Running Jobs', val: overview.running_jobs, icon: Zap, color: 'text-indigo-400', bg: 'bg-indigo-500/10', pulse: true },
    { title: 'Queued Jobs', val: overview.queued_jobs, icon: Clock, color: 'text-amber-400', bg: 'bg-amber-500/10' },
    { title: 'Success Rate', val: `${overview.success_rate_percent}%`, icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    { title: 'Active Workers', val: overview.active_workers, icon: Server, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    { title: 'Unhealthy Workers', val: overview.unhealthy_workers, icon: AlertTriangle, color: overview.unhealthy_workers > 0 ? 'text-rose-400' : 'text-slate-400', bg: overview.unhealthy_workers > 0 ? 'bg-rose-500/10' : 'bg-slate-500/10' },
    { title: 'Avg Latency', val: `${overview.avg_execution_time_ms} ms`, icon: TrendingUp, color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
  ];

  const pieData = status_distribution.map(item => ({
    name: item.status,
    value: item.count,
    color: STATUS_COLORS[item.status] || '#64748B'
  }));

  return (
    <div className="space-y-6">
      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {statCards.map((card, i) => (
          <div key={i} className="p-4 rounded-xl bg-dark-800/80 border border-dark-700/80 hover:border-dark-600 transition-all">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-medium text-slate-400 tracking-tight">{card.title}</span>
              <div className={`p-1.5 rounded-lg ${card.bg} ${card.color}`}>
                <card.icon className={`w-4 h-4 ${card.pulse ? 'animate-pulse' : ''}`} />
              </div>
            </div>
            <div className="text-xl font-bold text-white mt-2 font-mono">{card.val}</div>
          </div>
        ))}
      </div>

      {/* Analytics Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Job Execution Throughput Area Chart */}
        <div className="lg:col-span-2 p-5 rounded-2xl bg-dark-800/80 border border-dark-700/80">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-white text-base">Job Throughput & Execution Trends</h3>
              <p className="text-xs text-slate-400">Completed vs Failed tasks over time</p>
            </div>
            <span className="text-xs text-indigo-400 bg-indigo-500/10 px-2.5 py-1 rounded-lg border border-indigo-500/20 font-mono">
              Live Window
            </span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={throughput_history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCompleted" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366F1" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#6366F1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="timestamp" stroke="#64748B" fontSize={11} />
                <YAxis stroke="#64748B" fontSize={11} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.5rem', color: '#FFF' }}
                />
                <Area type="monotone" dataKey="completed" stroke="#6366F1" strokeWidth={2} fillOpacity={1} fill="url(#colorCompleted)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Job Status Distribution Pie */}
        <div className="p-5 rounded-2xl bg-dark-800/80 border border-dark-700/80 flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-white text-base mb-1">Job Status Breakdown</h3>
            <p className="text-xs text-slate-400">Current workload status metrics</p>
          </div>
          <div className="h-44 flex items-center justify-center my-2">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.5rem', color: '#FFF' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {pieData.map((item, i) => (
              <div key={i} className="flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-slate-400">{item.name}:</span>
                <span className="font-bold text-white font-mono">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Workers Grid and Recent Jobs Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Workers Health Panel */}
        <div className="p-5 rounded-2xl bg-dark-800/80 border border-dark-700/80">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-white text-base">Worker Cluster Nodes</h3>
            <Link to="/workers" className="text-xs text-indigo-400 hover:underline flex items-center">
              View All <ArrowUpRight className="w-3.5 h-3.5 ml-0.5" />
            </Link>
          </div>
          <div className="space-y-3">
            {workers.length === 0 ? (
              <div className="text-xs text-slate-500 py-6 text-center">No worker nodes registered</div>
            ) : (
              workers.map((w) => (
                <div key={w.id} className="p-3 rounded-xl bg-dark-900/60 border border-dark-700/60 flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-sm font-semibold text-white">{w.id}</span>
                      <StatusBadge status={w.status} />
                    </div>
                    <div className="text-xs text-slate-400 flex items-center space-x-2">
                      <span>Host: {w.hostname}</span>
                      <span>•</span>
                      <span>Jobs: {w.jobs_completed}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-emerald-400 font-mono flex items-center space-x-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping mr-1" />
                      Alive
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Jobs Table */}
        <div className="lg:col-span-2 p-5 rounded-2xl bg-dark-800/80 border border-dark-700/80">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-white text-base">Recent Jobs Stream</h3>
            <Link to="/jobs" className="text-xs text-indigo-400 hover:underline flex items-center">
              View Full Queue <ArrowUpRight className="w-3.5 h-3.5 ml-0.5" />
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-dark-700 text-slate-400 font-semibold uppercase tracking-wider">
                  <th className="py-2.5 px-3">Job ID</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Priority</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Retries</th>
                  <th className="py-2.5 px-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-700/50 text-slate-300">
                {recentJobs.map((job) => (
                  <tr key={job.id} className="hover:bg-dark-700/30 transition-colors">
                    <td className="py-3 px-3 font-mono font-medium text-white text-[11px]">
                      {job.id.substring(0, 8)}...
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded bg-dark-700 text-slate-300 font-mono text-[11px]">
                        {job.job_type}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className={`font-mono font-bold ${job.priority >= 8 ? 'text-rose-400' : job.priority >= 5 ? 'text-amber-400' : 'text-slate-400'}`}>
                        P{job.priority}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <StatusBadge status={job.status} />
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-400">
                      {job.retry_count}/{job.max_retries}
                    </td>
                    <td className="py-3 px-3">
                      <Link
                        to={`/jobs/${job.id}`}
                        className="text-indigo-400 hover:text-indigo-300 font-medium"
                      >
                        Inspect →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
