import React, { useEffect, useState } from 'react';
import { BarChart3, TrendingUp, Cpu, Server, Activity, ShieldCheck } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { metricsApi } from '../services/api';
import { SystemMetricsResponse } from '../types';

export const MetricsPage: React.FC<{ refreshTrigger: number }> = ({ refreshTrigger }) => {
  const [metrics, setMetrics] = useState<SystemMetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMetrics = async () => {
    try {
      const data = await metricsApi.getOverviewMetrics();
      setMetrics(data);
    } catch (e) {
      console.error("Failed to load metrics:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, [refreshTrigger]);

  if (loading || !metrics) {
    return <div className="py-12 text-center text-slate-500 text-xs">Loading analytics data...</div>;
  }

  const { overview, job_type_distribution } = metrics;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">System Performance & Analytics</h2>
        <p className="text-xs text-slate-400">Application-level monitoring, throughput, worker health, and queue latency metrics</p>
      </div>

      {/* Overview Analytics Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 rounded-2xl bg-dark-800/80 border border-dark-700/80 space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase">Average Latency</span>
          <div className="text-2xl font-bold text-cyan-400 font-mono">{overview.avg_execution_time_ms} ms</div>
          <span className="text-[11px] text-slate-500">Average execution duration across all successful attempts</span>
        </div>
        <div className="p-5 rounded-2xl bg-dark-800/80 border border-dark-700/80 space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase">Success Rate</span>
          <div className="text-2xl font-bold text-emerald-400 font-mono">{overview.success_rate_percent}%</div>
          <span className="text-[11px] text-slate-500">Ratio of succeeded jobs to total finished jobs</span>
        </div>
        <div className="p-5 rounded-2xl bg-dark-800/80 border border-dark-700/80 space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase">Active Cluster Nodes</span>
          <div className="text-2xl font-bold text-indigo-400 font-mono">{overview.active_workers} Nodes</div>
          <span className="text-[11px] text-slate-500">Workers sending heartbeats within 15s window</span>
        </div>
      </div>

      {/* Job Type Bar Chart */}
      <div className="p-6 rounded-2xl bg-dark-800/80 border border-dark-700/80 space-y-4">
        <h3 className="font-bold text-white text-base">Workload Type Distribution</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={job_type_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
              <XAxis dataKey="job_type" stroke="#64748B" fontSize={11} />
              <YAxis stroke="#64748B" fontSize={11} />
              <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.5rem', color: '#FFF' }} />
              <Bar dataKey="count" fill="#6366F1" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Prometheus Info Box */}
      <div className="p-5 rounded-2xl bg-dark-800/80 border border-dark-700/80 flex items-center justify-between text-xs">
        <div>
          <h4 className="font-bold text-white mb-1">Prometheus & Grafana Exporter</h4>
          <p className="text-slate-400">TaskFlow exposes open-telemetry metrics at <code className="text-indigo-400 font-mono">/api/metrics/prometheus</code></p>
        </div>
        <a
          href="/api/metrics/prometheus"
          target="_blank"
          rel="noreferrer"
          className="px-3 py-1.5 bg-dark-700 hover:bg-dark-600 text-slate-200 rounded-lg font-mono"
        >
          View Raw Metrics →
        </a>
      </div>
    </div>
  );
};
