import React from 'react';
import { Cpu, RefreshCw, Plus, ShieldCheck, Activity } from 'lucide-react';

interface NavbarProps {
  onOpenSubmitModal: () => void;
  autoRefresh: boolean;
  onToggleAutoRefresh: () => void;
  onManualRefresh: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  onOpenSubmitModal,
  autoRefresh,
  onToggleAutoRefresh,
  onManualRefresh
}) => {
  return (
    <header className="h-16 border-b border-dark-700 bg-dark-800/80 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-600 to-indigo-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <Cpu className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-lg text-white tracking-tight flex items-center gap-2">
            TaskFlow
            <span className="px-2 py-0.5 text-[10px] uppercase font-bold tracking-wider bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 rounded-full">
              Distributed v1.0
            </span>
          </h1>
          <p className="text-xs text-slate-400">Distributed Job Processing & ML Scheduler</p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* Auto Refresh Toggle */}
        <div className="flex items-center space-x-2 bg-dark-900 border border-dark-700 px-3 py-1.5 rounded-lg">
          <span className="text-xs text-slate-400 font-medium">Auto Polling</span>
          <button
            onClick={onToggleAutoRefresh}
            className={`w-9 h-5 rounded-full transition-colors relative p-0.5 ${autoRefresh ? 'bg-indigo-600' : 'bg-slate-700'}`}
          >
            <div className={`w-4 h-4 rounded-full bg-white transition-transform ${autoRefresh ? 'translate-x-4' : 'translate-x-0'}`} />
          </button>
        </div>

        {/* Refresh Button */}
        <button
          onClick={onManualRefresh}
          className="p-2 text-slate-400 hover:text-white bg-dark-700/50 hover:bg-dark-700 rounded-lg transition-colors border border-dark-600/50"
          title="Refresh Data"
        >
          <RefreshCw className="w-4 h-4" />
        </button>

        {/* Submit Job Button */}
        <button
          onClick={onOpenSubmitModal}
          className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-all shadow-lg shadow-indigo-600/25 active:scale-95"
        >
          <Plus className="w-4 h-4" />
          <span>Submit New Job</span>
        </button>
      </div>
    </header>
  );
};
