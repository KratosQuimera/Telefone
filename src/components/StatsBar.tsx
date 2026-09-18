import React from "react";
import { Phone, CheckCircle2, XCircle, TrendingUp, AlertTriangle } from "lucide-react";
import { Stats } from "../types";

interface StatsBarProps {
  stats: Stats;
}

export const StatsBar: React.FC<StatsBarProps> = ({ stats }) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2.5 mb-5">
      {/* Total */}
      <div className="bg-[#111827] p-3 rounded-xl border border-slate-800 shadow-xs flex items-center justify-between min-w-0">
        <div className="min-w-0">
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider truncate">Total Ramais</p>
          <p className="text-xl font-extrabold text-white mt-0.5">{stats.total}</p>
        </div>
        <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-300 shrink-0">
          <Phone className="w-4 h-4" />
        </div>
      </div>

      {/* Online */}
      <div className="bg-[#111827] p-3 rounded-xl border border-slate-800 shadow-xs flex items-center justify-between min-w-0">
        <div className="min-w-0">
          <p className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider truncate">Online</p>
          <div className="flex items-baseline gap-1.5 mt-0.5">
            <p className="text-xl font-extrabold text-emerald-400">{stats.online}</p>
            <span className="text-[10px] text-emerald-300 font-semibold">
              {stats.total ? Math.round((stats.online / stats.total) * 100) : 0}%
            </span>
          </div>
        </div>
        <div className="w-8 h-8 rounded-lg bg-emerald-950/80 border border-emerald-800/80 flex items-center justify-center text-emerald-400 shrink-0">
          <CheckCircle2 className="w-4 h-4" />
        </div>
      </div>

      {/* Offline */}
      <div className="bg-[#111827] p-3 rounded-xl border border-slate-800 shadow-xs flex items-center justify-between min-w-0">
        <div className="min-w-0">
          <p className="text-[10px] font-bold text-rose-400 uppercase tracking-wider truncate">Offline</p>
          <p className="text-xl font-extrabold text-rose-400 mt-0.5">{stats.offline}</p>
        </div>
        <div className="w-8 h-8 rounded-lg bg-rose-950/80 border border-rose-800/80 flex items-center justify-center text-rose-400 shrink-0">
          <XCircle className="w-4 h-4" />
        </div>
      </div>

      {/* SLA Global */}
      <div className="bg-[#111827] p-3 rounded-xl border border-slate-800 shadow-xs flex items-center justify-between min-w-0">
        <div className="min-w-0">
          <p className="text-[10px] font-bold text-sky-400 uppercase tracking-wider truncate">Disponibilidade</p>
          <div className="flex items-baseline gap-1 mt-0.5">
            <p className="text-xl font-extrabold text-sky-400">{stats.sla}%</p>
          </div>
        </div>
        <div className="w-8 h-8 rounded-lg bg-sky-950/80 border border-sky-800/80 flex items-center justify-center text-sky-400 shrink-0">
          <TrendingUp className="w-4 h-4" />
        </div>
      </div>

      {/* Incidentes */}
      <div className="bg-[#111827] p-3 rounded-xl border border-slate-800 shadow-xs flex items-center justify-between min-w-0 col-span-2 md:col-span-1">
        <div className="min-w-0">
          <p className="text-[10px] font-bold text-amber-400 uppercase tracking-wider truncate">Incidentes</p>
          <p className="text-xl font-extrabold text-amber-400 mt-0.5">{stats.incidentesAbertos}</p>
        </div>
        <div className="w-8 h-8 rounded-lg bg-amber-950/80 border border-amber-800/80 flex items-center justify-center text-amber-400 shrink-0">
          <AlertTriangle className="w-4 h-4" />
        </div>
      </div>
    </div>
  );
};
