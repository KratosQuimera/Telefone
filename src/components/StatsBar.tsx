import React from "react";
import { Phone, CheckCircle2, XCircle, TrendingUp, AlertTriangle } from "lucide-react";
import { Stats } from "../types";

interface StatsBarProps {
  stats: Stats;
}

export const StatsBar: React.FC<StatsBarProps> = ({ stats }) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 mb-6">
      {/* Total */}
      <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-xs flex items-center justify-between">
        <div>
          <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Total Ramais</p>
          <p className="text-2xl font-bold text-slate-900 mt-0.5">{stats.total}</p>
        </div>
        <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center text-slate-600">
          <Phone className="w-5 h-5" />
        </div>
      </div>

      {/* Online */}
      <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-xs flex items-center justify-between">
        <div>
          <p className="text-[11px] font-semibold text-emerald-700 uppercase tracking-wider">Online</p>
          <div className="flex items-baseline gap-2 mt-0.5">
            <p className="text-2xl font-bold text-emerald-700">{stats.online}</p>
            <span className="text-xs text-emerald-600 font-medium">
              {stats.total ? Math.round((stats.online / stats.total) * 100) : 0}%
            </span>
          </div>
        </div>
        <div className="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600">
          <CheckCircle2 className="w-5 h-5" />
        </div>
      </div>

      {/* Offline */}
      <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-xs flex items-center justify-between">
        <div>
          <p className="text-[11px] font-semibold text-rose-600 uppercase tracking-wider">Offline</p>
          <p className="text-2xl font-bold text-rose-600 mt-0.5">{stats.offline}</p>
        </div>
        <div className="w-10 h-10 rounded-lg bg-rose-50 flex items-center justify-center text-rose-600">
          <XCircle className="w-5 h-5" />
        </div>
      </div>

      {/* SLA Global */}
      <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-xs flex items-center justify-between">
        <div>
          <p className="text-[11px] font-semibold text-sky-700 uppercase tracking-wider">Disponibilidade SLA</p>
          <div className="flex items-baseline gap-1 mt-0.5">
            <p className="text-2xl font-bold text-sky-900">{stats.sla}%</p>
          </div>
        </div>
        <div className="w-10 h-10 rounded-lg bg-sky-50 flex items-center justify-center text-sky-600">
          <TrendingUp className="w-5 h-5" />
        </div>
      </div>

      {/* Incidentes */}
      <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-xs flex items-center justify-between">
        <div>
          <p className="text-[11px] font-semibold text-indigo-700 uppercase tracking-wider">Incidentes</p>
          <p className="text-2xl font-bold text-indigo-900 mt-0.5">{stats.incidentesAbertos}</p>
        </div>
        <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600">
          <AlertTriangle className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
};
