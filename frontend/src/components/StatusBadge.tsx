import React from 'react';
import { JobStatus, WorkerStatus } from '../types';

interface StatusBadgeProps {
  status: JobStatus | WorkerStatus | string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'sm' }) => {
  let style = 'bg-slate-800 text-slate-300 border-slate-700';

  switch (status) {
    case 'SUCCESS':
    case 'IDLE':
      style = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      break;
    case 'RUNNING':
    case 'BUSY':
      style = 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30 animate-pulse';
      break;
    case 'QUEUED':
    case 'PENDING':
      style = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      break;
    case 'RETRYING':
      style = 'bg-purple-500/10 text-purple-400 border-purple-500/30 animate-pulse';
      break;
    case 'FAILED':
    case 'UNHEALTHY':
    case 'DEAD_LETTER':
      style = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      break;
    case 'CANCELLED':
    case 'STOPPED':
      style = 'bg-slate-500/10 text-slate-400 border-slate-500/30';
      break;
  }

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
    lg: 'px-3 py-1 text-sm'
  };

  return (
    <span className={`inline-flex items-center font-mono font-medium rounded-md border ${style} ${sizeStyles[size]}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5 opacity-75" />
      {status}
    </span>
  );
};
