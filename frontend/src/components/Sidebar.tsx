import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, ListFilter, Server, Calendar, AlertOctagon, BarChart3 } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navItems = [
    { to: '/', label: 'Overview Dashboard', icon: LayoutDashboard },
    { to: '/jobs', label: 'Jobs Explorer', icon: ListFilter },
    { to: '/workers', label: 'Worker Nodes', icon: Server },
    { to: '/schedules', label: 'Cron Schedules', icon: Calendar },
    { to: '/dead-letter', label: 'Dead Letter Queue', icon: AlertOctagon },
    { to: '/metrics', label: 'System Analytics', icon: BarChart3 },
  ];

  return (
    <aside className="w-64 border-r border-dark-700 bg-dark-800/50 min-h-[calc(100vh-4rem)] p-4 flex flex-col justify-between">
      <div className="space-y-1">
        <div className="px-3 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Management
        </div>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-dark-700/50'
              }`
            }
          >
            <item.icon className="w-4 h-4" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </div>

      <div className="p-3 bg-dark-900/60 rounded-xl border border-dark-700/60 text-xs text-slate-400 space-y-2">
        <div className="font-semibold text-slate-300">Cluster Status</div>
        <div className="flex justify-between items-center text-slate-400">
          <span>Engine</span>
          <span className="text-emerald-400 font-mono">Redis + Postgres</span>
        </div>
        <div className="flex justify-between items-center text-slate-400">
          <span>Object Store</span>
          <span className="text-indigo-400 font-mono">MinIO S3</span>
        </div>
      </div>
    </aside>
  );
};
