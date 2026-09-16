import React, { useState } from "react";
import { 
  Phone, 
  Wifi, 
  WifiOff, 
  MapPin, 
  Tag, 
  MoreVertical, 
  Edit, 
  Trash2, 
  RefreshCw,
  Cpu
} from "lucide-react";
import { Ramal, Usuario } from "../types";

interface RamalCardProps {
  ramal: Ramal;
  usuario: Usuario | null;
  onEdit: (ramal: Ramal) => void;
  onDelete: (id: number) => void;
  onPing: (id: number) => Promise<void>;
}

export const RamalCard: React.FC<RamalCardProps> = ({
  ramal,
  usuario,
  onEdit,
  onDelete,
  onPing,
}) => {
  const [isPinging, setIsPinging] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const handlePing = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsPinging(true);
    try {
      await onPing(ramal.id);
    } finally {
      setIsPinging(false);
    }
  };

  const isOnline = ramal.status === "ONLINE";

  const statusConfig = isOnline
    ? {
        bg: "bg-emerald-50 text-emerald-700 border-emerald-200",
        dot: "bg-emerald-500",
        label: "Online",
        border: "border-emerald-200",
        cardIcon: "bg-emerald-100 text-emerald-900",
      }
    : {
        bg: "bg-rose-50 text-rose-700 border-rose-200",
        dot: "bg-rose-500",
        label: "Offline",
        border: "border-rose-200",
        cardIcon: "bg-rose-100 text-rose-900",
      };

  return (
    <div className={`bg-white rounded-xl border ${statusConfig.border} shadow-xs hover:shadow-md transition-all p-4 relative flex flex-col justify-between`}>
      <div>
        {/* Top Header: Ramal & Status */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2.5">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-base ${statusConfig.cardIcon}`}>
              <Phone className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-slate-900 text-lg tracking-tight">
                  Ramal {ramal.numero}
                </span>
              </div>
              <p className="text-xs font-medium text-slate-500 flex items-center gap-1">
                <Cpu className="w-3 h-3 text-slate-400" />
                {ramal.modelo || "Cisco CP-7841"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${statusConfig.bg}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${statusConfig.dot} ${isOnline ? "animate-pulse" : ""}`} />
              {statusConfig.label}
            </span>

            {/* Menu de ações (sensível: se não autenticado, App.tsx solicita senha) */}
            <div className="relative">
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded"
                title="Opções do ramal"
              >
                <MoreVertical className="w-4 h-4" />
              </button>
              {menuOpen && (
                <div 
                  onMouseLeave={() => setMenuOpen(false)}
                  className="absolute right-0 mt-1 w-32 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-20"
                >
                  <button
                    onClick={() => { setMenuOpen(false); onEdit(ramal); }}
                    className="w-full text-left px-3 py-1.5 text-xs text-slate-700 hover:bg-slate-50 flex items-center gap-2"
                  >
                    <Edit className="w-3.5 h-3.5" /> Editar
                  </button>
                  <button
                    onClick={() => { setMenuOpen(false); onDelete(ramal.id); }}
                    className="w-full text-left px-3 py-1.5 text-xs text-rose-600 hover:bg-rose-50 flex items-center gap-2"
                  >
                    <Trash2 className="w-3.5 h-3.5" /> Excluir
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Descrição */}
        <h4 className="font-semibold text-slate-800 text-sm mb-3 line-clamp-1" title={ramal.descricao}>
          {ramal.descricao}
        </h4>

        {/* Informações detalhadas */}
        <div className="space-y-1.5 text-xs text-slate-600 bg-slate-50/70 p-2.5 rounded-lg border border-slate-100">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 flex items-center gap-1">
              <MapPin className="w-3 h-3" /> Bloco:
            </span>
            <span className="font-medium text-slate-700">{ramal.bloco}</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-slate-400 flex items-center gap-1">
              <Tag className="w-3 h-3" /> Setor:
            </span>
            <span className="font-medium text-slate-700">{ramal.setor}</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-slate-400">IP:</span>
            <code className="font-mono text-[11px] text-slate-800 bg-white px-1.5 py-0.5 rounded border border-slate-200">
              {ramal.ip}
            </code>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-slate-400">MAC Cisco:</span>
            <code className="font-mono text-[11px] text-slate-600">
              {ramal.mac_cisco}
            </code>
          </div>
        </div>
      </div>

      {/* Footer com Latência & Ping */}
      <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs">
          {isOnline ? (
            <span className="text-emerald-700 font-semibold flex items-center gap-1">
              <Wifi className="w-3.5 h-3.5" />
              {ramal.latencia_ms ? `${ramal.latencia_ms}ms` : "Conectado"}
            </span>
          ) : (
            <span className="text-rose-600 font-medium flex items-center gap-1">
              <WifiOff className="w-3.5 h-3.5" />
              Indisponível
            </span>
          )}
        </div>

        <button
          onClick={handlePing}
          disabled={isPinging}
          title="Executar teste de ping rápido"
          className="flex items-center gap-1 text-[11px] font-semibold text-slate-600 hover:text-emerald-700 bg-slate-100 hover:bg-emerald-50 px-2 py-1 rounded transition border border-slate-200"
        >
          <RefreshCw className={`w-3 h-3 ${isPinging ? "animate-spin text-emerald-600" : ""}`} />
          <span>{isPinging ? "Testando..." : "Ping"}</span>
        </button>
      </div>
    </div>
  );
};
